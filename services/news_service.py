"""
services/news_service.py

XAU AI SIGNAL BOT
=================

NEWS SERVICE

Fungsi:
- Mengambil berita terbaru XAUUSD / Gold
- Menggunakan NewsAPI
- Filter berita relevan dengan Gold
- Filter berita yang terlalu lama
- Filter blocked keywords
- Prioritas source terpercaya
- Mencegah duplicate
- Mengembalikan 1 berita terbaik
- Tidak mengubah sistem SMC lama

Digunakan oleh:
- Fundamental AI
- Combined AI

CATATAN:
API KEY disimpan di .env

NEWS_API_KEY=xxxx
NEWS_API_URL=https://newsapi.org/v2/everything
"""

import json
import logging
import os

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from config.settings import (
    NEWS_API_KEY,
    NEWS_API_URL,

    FUNDAMENTAL_NEWS_PER_UPDATE,
    FUNDAMENTAL_MAX_NEWS_AGE_HOURS,
    FUNDAMENTAL_BLOCKED_KEYWORDS,
    FUNDAMENTAL_SEARCH_KEYWORDS,
    FUNDAMENTAL_SOURCE_PRIORITY,
    FUNDAMENTAL_NEWS_CACHE_FILE,

    COMBINED_NEWS_PER_UPDATE,
    COMBINED_MAX_NEWS_AGE_HOURS,
    COMBINED_NEWS_CACHE_FILE,

    NEWS_REQUEST_TIMEOUT,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONSTANT
# =========================================================

DEFAULT_NEWS_API_URL = (
    "https://newsapi.org/v2/everything"
)


# =========================================================
# SOURCE SCORE
# =========================================================

SOURCE_PRIORITY_SCORE = {

    "reuters": 100,

    "bloomberg": 95,

    "cnbc": 90,

    "wall street journal": 90,

    "financial times": 90,

    "investing.com": 80,

    "fxstreet": 80,

}


# =========================================================
# HELPERS
# =========================================================

def _normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value).strip()


# =========================================================
# PARSE DATE
# =========================================================

def _parse_published_at(
    value: str,
) -> Optional[datetime]:

    if not value:
        return None

    try:

        value = value.strip()

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        dt = datetime.fromisoformat(value)

        if dt.tzinfo is None:
            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:

        logger.warning(
            "Tidak dapat membaca publishedAt: %s",
            value,
        )

        return None


# =========================================================
# CACHE DIRECTORY
# =========================================================

def _ensure_cache_directory(
    cache_file: str,
) -> None:

    try:

        path = Path(
            cache_file
        )

        if path.parent:

            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

    except Exception:

        logger.exception(
            "Gagal membuat folder cache."
        )


# =========================================================
# LOAD CACHE
# =========================================================

def load_news_cache(
    cache_file: str,
) -> List[str]:

    try:

        path = Path(
            cache_file
        )

        if not path.exists():

            return []

        with path.open(
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if not isinstance(
            data,
            list,
        ):

            return []

        return [
            str(item)
            for item in data
        ]

    except Exception:

        logger.exception(
            "Gagal membaca news cache: %s",
            cache_file,
        )

        return []


# =========================================================
# SAVE CACHE
# =========================================================

def save_news_cache(
    cache_file: str,
    cache: List[str],
) -> None:

    try:

        _ensure_cache_directory(
            cache_file
        )

        # Jangan biarkan cache tumbuh tanpa batas.

        cache = list(
            dict.fromkeys(
                cache
            )
        )[-500:]

        path = Path(
            cache_file
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                cache,
                f,
                ensure_ascii=False,
                indent=2,
            )

    except Exception:

        logger.exception(
            "Gagal menyimpan news cache: %s",
            cache_file,
        )


# =========================================================
# ARTICLE ID
# =========================================================

def get_article_id(
    article: Dict[str, Any],
) -> str:

    url = _normalize_text(
        article.get("url")
    )

    if url:
        return url

    title = _normalize_text(
        article.get("title")
    )

    published = _normalize_text(
        article.get("publishedAt")
    )

    return (
        f"{title}|{published}"
    )


# =========================================================
# BUILD SEARCH QUERY
# =========================================================

def build_news_query(
    keywords: List[str],
) -> str:

    cleaned = []

    for keyword in keywords:

        keyword = _normalize_text(
            keyword
        )

        if not keyword:
            continue

        # Exact phrase untuk keyword
        # yang mempunyai spasi.

        if " " in keyword:

            cleaned.append(
                f'"{keyword}"'
            )

        else:

            cleaned.append(
                keyword
            )

    # NewsAPI mendukung OR.
    # Query tetap dijaga agar tidak terlalu panjang.

    query = " OR ".join(
        cleaned
    )

    return query[:480]


# =========================================================
# FETCH NEWS FROM API
# =========================================================

def fetch_news(
    keywords: Optional[List[str]] = None,
    max_age_hours: int = 24,
    page_size: int = 10,
) -> List[Dict[str, Any]]:

    # =====================================================
    # API KEY
    # =====================================================

    api_key = _normalize_text(
        NEWS_API_KEY
    )

    if not api_key:

        logger.error(
            "NEWS_API_KEY belum dikonfigurasi."
        )

        return []


    # =====================================================
    # API URL
    # =====================================================

    api_url = _normalize_text(
        NEWS_API_URL
    )

    if not api_url:

        api_url = (
            DEFAULT_NEWS_API_URL
        )


    # =====================================================
    # KEYWORDS
    # =====================================================

    if keywords is None:

        keywords = (
            FUNDAMENTAL_SEARCH_KEYWORDS
        )


    query = build_news_query(
        keywords
    )

    if not query:

        logger.warning(
            "News query kosong."
        )

        return []


    # =====================================================
    # TIME WINDOW
    # =====================================================

    now = datetime.now(
        timezone.utc
    )

    from_time = (
        now
        - timedelta(
            hours=max_age_hours
        )
    )


    # =====================================================
    # PARAMETERS
    # =====================================================

    params = {

        "q": query,

        "from": from_time.isoformat(),

        "to": now.isoformat(),

        "language": "en",

        "sortBy": "publishedAt",

        "pageSize": max(
            1,
            min(
                int(page_size),
                100,
            ),
        ),

        "page": 1,

        "apiKey": api_key,

    }


    # =====================================================
    # REQUEST
    # =====================================================

    try:

        logger.info(
            "Mengambil berita XAU | "
            "query=%s",
            query,
        )

        response = requests.get(

            api_url,

            params=params,

            timeout=NEWS_REQUEST_TIMEOUT,

        )


        # =================================================
        # HTTP ERROR
        # =================================================

        response.raise_for_status()


        # =================================================
        # JSON
        # =================================================

        data = response.json()


    except requests.RequestException:

        logger.exception(
            "Request NewsAPI gagal."
        )

        return []


    except ValueError:

        logger.exception(
            "Response NewsAPI bukan JSON valid."
        )

        return []


    except Exception:

        logger.exception(
            "Error tidak diketahui ketika mengambil berita."
        )

        return []


    # =====================================================
    # API STATUS
    # =====================================================

    if data.get("status") != "ok":

        logger.error(
            "NewsAPI error | %s",
            data,
        )

        return []


    # =====================================================
    # ARTICLES
    # =====================================================

    articles = data.get(
        "articles",
        []
    )

    if not isinstance(
        articles,
        list,
    ):

        return []


    logger.info(
        "NewsAPI mengembalikan %s artikel.",
        len(articles),
    )


    return articles


# =========================================================
# BLOCKED KEYWORD CHECK
# =========================================================

def contains_blocked_keyword(
    article: Dict[str, Any],
) -> bool:

    title = _normalize_text(
        article.get("title")
    )

    description = _normalize_text(
        article.get("description")
    )

    content = _normalize_text(
        article.get("content")
    )

    text = (
        f"{title} "
        f"{description} "
        f"{content}"
    ).lower()


    for keyword in (
        FUNDAMENTAL_BLOCKED_KEYWORDS
    ):

        keyword = _normalize_text(
            keyword
        ).lower()

        if not keyword:
            continue

        if keyword in text:

            logger.info(
                "Berita diblokir | keyword=%s | title=%s",
                keyword,
                title,
            )

            return True


    return False


# =========================================================
# GOLD RELEVANCE CHECK
# =========================================================

def is_gold_relevant(
    article: Dict[str, Any],
) -> bool:

    title = _normalize_text(
        article.get("title")
    )

    description = _normalize_text(
        article.get("description")
    )

    content = _normalize_text(
        article.get("content")
    )

    text = (
        f"{title} "
        f"{description} "
        f"{content}"
    ).lower()


    relevance_keywords = [

        "gold",

        "xau",

        "xauusd",

        "us dollar",

        "usd",

        "federal reserve",

        "fed",

        "interest rate",

        "treasury yield",

        "bond yield",

        "inflation",

        "monetary policy",

        "central bank",

        "geopolitical",

        "geopolitics",

        "middle east",

        "war",

    ]


    for keyword in relevance_keywords:

        if keyword in text:

            return True


    return False


# =========================================================
# AGE CHECK
# =========================================================

def is_article_recent(
    article: Dict[str, Any],
    max_age_hours: int,
) -> bool:

    published_at = _parse_published_at(
        _normalize_text(
            article.get(
                "publishedAt"
            )
        )
    )

    if published_at is None:

        return False


    now = datetime.now(
        timezone.utc
    )

    age = (
        now
        - published_at
    )


    if age.total_seconds() < 0:

        # Artikel sedikit di masa depan
        # akibat perbedaan clock masih diterima.

        return True


    return (
        age
        <= timedelta(
            hours=max_age_hours
        )
    )


# =========================================================
# SOURCE SCORE
# =========================================================

def get_source_score(
    article: Dict[str, Any],
) -> int:

    source = article.get(
        "source"
    )

    if not isinstance(
        source,
        dict,
    ):

        return 0


    name = _normalize_text(
        source.get("name")
    ).lower()


    if not name:
        return 0


    # Exact / partial matching.

    for source_name, score in (
        SOURCE_PRIORITY_SCORE.items()
    ):

        if source_name in name:

            return score


    # Fallback untuk source lain.

    return 20


# =========================================================
# RECENCY SCORE
# =========================================================

def get_recency_score(
    article: Dict[str, Any],
) -> int:

    published_at = _parse_published_at(
        _normalize_text(
            article.get(
                "publishedAt"
            )
        )
    )

    if published_at is None:

        return 0


    now = datetime.now(
        timezone.utc
    )

    age_minutes = max(
        0,
        int(
            (
                now
                - published_at
            ).total_seconds()
            / 60
        ),
    )


    # Berita lebih baru mendapatkan score lebih tinggi.

    if age_minutes <= 15:
        return 100

    if age_minutes <= 30:
        return 90

    if age_minutes <= 60:
        return 80

    if age_minutes <= 120:
        return 65

    if age_minutes <= 360:
        return 45

    if age_minutes <= 720:
        return 30

    return 15


# =========================================================
# RELEVANCE SCORE
# =========================================================

def get_relevance_score(
    article: Dict[str, Any],
) -> int:

    title = _normalize_text(
        article.get("title")
    ).lower()

    description = _normalize_text(
        article.get("description")
    ).lower()

    content = _normalize_text(
        article.get("content")
    ).lower()


    score = 0


    # Title jauh lebih penting.

    for keyword in (
        FUNDAMENTAL_SEARCH_KEYWORDS
    ):

        keyword = _normalize_text(
            keyword
        ).lower()

        if not keyword:
            continue


        if keyword in title:

            score += 30


        elif keyword in description:

            score += 10


        elif keyword in content:

            score += 5


    return min(
        score,
        150,
    )


# =========================================================
# TOTAL ARTICLE SCORE
# =========================================================

def calculate_article_score(
    article: Dict[str, Any],
) -> int:

    source_score = (
        get_source_score(
            article
        )
    )

    recency_score = (
        get_recency_score(
            article
        )
    )

    relevance_score = (
        get_relevance_score(
            article
        )
    )


    total = (
        source_score
        + recency_score
        + relevance_score
    )


    return total


# =========================================================
# FILTER ARTICLES
# =========================================================

def filter_articles(
    articles: List[Dict[str, Any]],
    max_age_hours: int,
    cache_file: str,
) -> List[Dict[str, Any]]:

    cache = set(
        load_news_cache(
            cache_file
        )
    )


    filtered = []


    for article in articles:

        if not isinstance(
            article,
            dict,
        ):

            continue


        # =================================================
        # REQUIRED DATA
        # =================================================

        title = _normalize_text(
            article.get("title")
        )

        url = _normalize_text(
            article.get("url")
        )

        published_at = _normalize_text(
            article.get(
                "publishedAt"
            )
        )


        if not title:

            continue


        if not url:

            continue


        if not published_at:

            continue


        # =================================================
        # DUPLICATE
        # =================================================

        article_id = get_article_id(
            article
        )

        if article_id in cache:

            logger.info(
                "Skip duplicate news | %s",
                title,
            )

            continue


        # =================================================
        # RECENT
        # =================================================

        if not is_article_recent(
            article,
            max_age_hours,
        ):

            continue


        # =================================================
        # BLOCKED
        # =================================================

        if contains_blocked_keyword(
            article
        ):

            continue


        # =================================================
        # GOLD RELEVANT
        # =================================================

        if not is_gold_relevant(
            article
        ):

            continue


        # =================================================
        # SCORE
        # =================================================

        article["_score"] = (
            calculate_article_score(
                article
            )
        )


        filtered.append(
            article
        )


    # =====================================================
    # SORT
    # =====================================================

    filtered.sort(

        key=lambda item: (

            item.get(
                "_score",
                0
            ),

            item.get(
                "publishedAt",
                ""
            ),

        ),

        reverse=True,

    )


    return filtered


# =========================================================
# GET LATEST FUNDAMENTAL NEWS
# =========================================================

def get_latest_fundamental_news(
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:

    if limit is None:

        limit = (
            FUNDAMENTAL_NEWS_PER_UPDATE
        )


    articles = fetch_news(

        keywords=(
            FUNDAMENTAL_SEARCH_KEYWORDS
        ),

        max_age_hours=(
            FUNDAMENTAL_MAX_NEWS_AGE_HOURS
        ),

        page_size=10,

    )


    if not articles:

        return []


    filtered = filter_articles(

        articles,

        max_age_hours=(
            FUNDAMENTAL_MAX_NEWS_AGE_HOURS
        ),

        cache_file=(
            FUNDAMENTAL_NEWS_CACHE_FILE
        ),

    )


    selected = filtered[
        :max(
            1,
            int(limit)
        )
    ]


    # =====================================================
    # SAVE CACHE
    # =====================================================

    if selected:

        cache = load_news_cache(
            FUNDAMENTAL_NEWS_CACHE_FILE
        )


        for article in selected:

            article_id = (
                get_article_id(
                    article
                )
            )

            if article_id:

                cache.append(
                    article_id
                )


        save_news_cache(

            FUNDAMENTAL_NEWS_CACHE_FILE,

            cache,

        )


    return selected


# =========================================================
# GET LATEST COMBINED NEWS
# =========================================================

def get_latest_combined_news(
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:

    if limit is None:

        limit = (
            COMBINED_NEWS_PER_UPDATE
        )


    articles = fetch_news(

        keywords=(
            FUNDAMENTAL_SEARCH_KEYWORDS
        ),

        max_age_hours=(
            COMBINED_MAX_NEWS_AGE_HOURS
        ),

        page_size=10,

    )


    if not articles:

        return []


    filtered = filter_articles(

        articles,

        max_age_hours=(
            COMBINED_MAX_NEWS_AGE_HOURS
        ),

        cache_file=(
            COMBINED_NEWS_CACHE_FILE
        ),

    )


    selected = filtered[
        :max(
            1,
            int(limit)
        )
    ]


    # =====================================================
    # SAVE CACHE
    # =====================================================

    if selected:

        cache = load_news_cache(
            COMBINED_NEWS_CACHE_FILE
        )


        for article in selected:

            article_id = (
                get_article_id(
                    article
                )
            )

            if article_id:

                cache.append(
                    article_id
                )


        save_news_cache(

            COMBINED_NEWS_CACHE_FILE,

            cache,

        )


    return selected


# =========================================================
# GET ONE LATEST NEWS
# =========================================================

def get_one_latest_news() -> Optional[Dict[str, Any]]:

    news = get_latest_fundamental_news(
        limit=1
    )


    if not news:

        return None


    return news[0]


# =========================================================
# FORMAT ARTICLE DATA
# =========================================================

def normalize_article(
    article: Dict[str, Any],
) -> Dict[str, Any]:

    source = article.get(
        "source"
    )

    if not isinstance(
        source,
        dict,
    ):

        source = {}


    return {

        "id": get_article_id(
            article
        ),

        "title": _normalize_text(
            article.get(
                "title"
            )
        ),

        "description": _normalize_text(
            article.get(
                "description"
            )
        ),

        "content": _normalize_text(
            article.get(
                "content"
            )
        ),

        "source": _normalize_text(
            source.get(
                "name"
            )
        ),

        "author": _normalize_text(
            article.get(
                "author"
            )
        ),

        "published_at": _normalize_text(
            article.get(
                "publishedAt"
            )
        ),

        "url": _normalize_text(
            article.get(
                "url"
            )
        ),

        "image_url": _normalize_text(
            article.get(
                "urlToImage"
            )
        ),

        "score": article.get(
            "_score",
            0
        ),

    }


# =========================================================
# TEST FUNCTION
# =========================================================

def test_news_service() -> None:

    logger.info(
        "======================================"
    )

    logger.info(
        "TEST NEWS SERVICE"
    )

    logger.info(
        "======================================"
    )


    news = (
        get_latest_fundamental_news(
            limit=1
        )
    )


    if not news:

        logger.warning(
            "Tidak ada berita valid."
        )

        return


    article = normalize_article(
        news[0]
    )


    logger.info(
        "NEWS TERPILIH"
    )

    logger.info(
        "Title   : %s",
        article["title"],
    )

    logger.info(
        "Source  : %s",
        article["source"],
    )

    logger.info(
        "Published: %s",
        article["published_at"],
    )

    logger.info(
        "Score   : %s",
        article["score"],
    )

    logger.info(
        "URL     : %s",
        article["url"],
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(name)s: "
            "%(message)s"
        ),
    )

    test_news_service()
