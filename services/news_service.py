"""
services/news_service.py

XAU AI SIGNAL BOT
=================

NEWS SERVICE

Fungsi:
- Mengambil berita terbaru
- Memfilter berita yang relevan dengan XAUUSD / Gold
- Memprioritaskan sumber terpercaya
- Menolak berita FOMC / NFP / PPI / CPI
- Mengecek umur berita
- Mengecek URL artikel asli
- Mencegah berita duplikat
- Menyediakan 1 berita terbaik
- Menyediakan data untuk Fundamental AI
- Menyediakan data untuk Combined AI

CATATAN:
- Tidak mengubah SMC.
- Tidak menghitung Entry.
- Tidak menghitung SL.
- Tidak menghitung TP.
- Tidak menentukan BUY / SELL.
- SMC tetap ditangani oleh signal_builder.py.
"""

import hashlib
import json
import logging
import os
import re

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

from config.settings import (
    NEWS_API_KEY,
    NEWS_API_URL,

    NEWS_SOURCE_LANGUAGE,
    NEWS_OUTPUT_LANGUAGE,

    NEWS_FETCH_LIMIT,
    NEWS_MAX_AGE_MINUTES,

    NEWS_KEYWORDS,

    NEWS_REQUIRE_SOURCE,
    NEWS_REQUIRE_URL,

    NEWS_PREVENT_DUPLICATE,

    FUNDAMENTAL_MAX_NEWS_AGE_HOURS,
    FUNDAMENTAL_BLOCKED_KEYWORDS,
    FUNDAMENTAL_SEARCH_KEYWORDS,
    FUNDAMENTAL_SOURCE_PRIORITY,

    FUNDAMENTAL_NEWS_CACHE_FILE,
    COMBINED_NEWS_CACHE_FILE,

    NEWS_REQUEST_TIMEOUT,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONSTANT
# =========================================================

DEFAULT_NEWS_LIMIT = 10

MAX_CACHE_ITEMS = 500

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/151.0 Safari/537.36"
)


# =========================================================
# SESSION
# =========================================================

_http_session = requests.Session()

_http_session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "application/json,text/plain,*/*",
    }
)


# =========================================================
# TIMEZONE
# =========================================================

WIB = timezone(
    timedelta(
        hours=7
    )
)


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = str(
        value
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# URL VALIDATION
# =========================================================

def is_valid_url(
    url: Any,
) -> bool:

    url = normalize_text(
        url
    )

    if not url:
        return False

    try:

        parsed = urlparse(
            url
        )

        return (
            parsed.scheme
            in (
                "http",
                "https",
            )
            and bool(
                parsed.netloc
            )
        )

    except Exception:

        return False


# =========================================================
# DATE PARSER
# =========================================================

def parse_datetime(
    value: Any,
) -> Optional[datetime]:

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):

        dt = value

    else:

        text = normalize_text(
            value
        )

        if not text:
            return None

        # ---------------------------------------------
        # ISO FORMAT
        # ---------------------------------------------

        try:

            normalized = (
                text
                .replace(
                    "Z",
                    "+00:00",
                )
            )

            dt = datetime.fromisoformat(
                normalized
            )

        except Exception:

            dt = None

        # ---------------------------------------------
        # COMMON FORMATS
        # ---------------------------------------------

        if dt is None:

            formats = [

                "%Y-%m-%dT%H:%M:%S.%fZ",

                "%Y-%m-%dT%H:%M:%SZ",

                "%Y-%m-%dT%H:%M:%S",

                "%Y-%m-%d %H:%M:%S",

                "%Y-%m-%d %H:%M",

                "%Y/%m/%d %H:%M:%S",

                "%Y/%m/%d %H:%M",

            ]

            for fmt in formats:

                try:

                    dt = datetime.strptime(
                        text,
                        fmt,
                    )

                    break

                except ValueError:

                    continue

    if dt is None:
        return None

    # ---------------------------------------------
    # FORCE UTC WHEN TIMEZONE IS MISSING
    # ---------------------------------------------

    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt


# =========================================================
# FORMAT DATETIME
# =========================================================

def format_datetime_wib(
    value: Any,
) -> str:

    dt = parse_datetime(
        value
    )

    if dt is None:
        return ""

    try:

        return dt.astimezone(
            WIB
        ).strftime(
            "%d-%m-%Y %H:%M WIB"
        )

    except Exception:

        return ""


# =========================================================
# NEWS AGE
# =========================================================

def news_age_minutes(
    published_at: Any,
) -> Optional[float]:

    dt = parse_datetime(
        published_at
    )

    if dt is None:
        return None

    now = datetime.now(
        timezone.utc
    )

    difference = (
        now - dt.astimezone(
            timezone.utc
        )
    )

    return difference.total_seconds() / 60


# =========================================================
# KEYWORD MATCH
# =========================================================

def keyword_match(
    text: str,
    keywords: List[str],
) -> List[str]:

    text_lower = normalize_text(
        text
    ).lower()

    matches = []

    for keyword in keywords:

        keyword = normalize_text(
            keyword
        )

        if not keyword:
            continue

        if keyword.lower() in text_lower:

            matches.append(
                keyword
            )

    return matches


# =========================================================
# BLOCKED NEWS
# =========================================================

def is_blocked_news(
    title: str,
    description: str = "",
    content: str = "",
) -> bool:

    combined_text = " ".join(
        [
            normalize_text(title),
            normalize_text(description),
            normalize_text(content),
        ]
    )

    matches = keyword_match(
        combined_text,
        FUNDAMENTAL_BLOCKED_KEYWORDS,
    )

    if matches:

        logger.info(
            "Berita diblokir | keywords=%s | title=%s",
            matches,
            title,
        )

        return True

    return False


# =========================================================
# RELEVANT NEWS
# =========================================================

def is_relevant_news(
    title: str,
    description: str = "",
    content: str = "",
) -> bool:

    combined_text = " ".join(
        [
            normalize_text(title),
            normalize_text(description),
            normalize_text(content),
        ]
    )

    # ---------------------------------------------
    # KEYWORD DARI SETTINGS
    # ---------------------------------------------

    matches_1 = keyword_match(
        combined_text,
        NEWS_KEYWORDS,
    )

    # ---------------------------------------------
    # KEYWORD FUNDAMENTAL
    # ---------------------------------------------

    matches_2 = keyword_match(
        combined_text,
        FUNDAMENTAL_SEARCH_KEYWORDS,
    )

    matches = list(
        dict.fromkeys(
            matches_1 + matches_2
        )
    )

    if matches:

        return True

    return False


# =========================================================
# SOURCE SCORE
# =========================================================

def source_score(
    source: str,
) -> int:

    source = normalize_text(
        source
    )

    if not source:
        return 0

    source_lower = source.lower()

    # ---------------------------------------------
    # EXACT / PRIORITY
    # ---------------------------------------------

    for index, priority in enumerate(
        FUNDAMENTAL_SOURCE_PRIORITY
    ):

        if priority.lower() in source_lower:

            # Sumber pertama = score tertinggi
            return 100 - (
                index * 5
            )

    # ---------------------------------------------
    # OTHER TRUSTED SOURCES
    # ---------------------------------------------

    trusted = [

        "marketwatch",

        "yahoo finance",

        "kitco",

        "forex.com",

        "dailyfx",

        "bloomberg",

        "cnbc",

        "reuters",

    ]

    for name in trusted:

        if name in source_lower:

            return 60

    return 20


# =========================================================
# NEWS ID
# =========================================================

def generate_news_id(
    news: Dict[str, Any],
) -> str:

    source = normalize_text(
        news.get(
            "source"
        )
    )

    title = normalize_text(
        news.get(
            "title"
        )
    )

    url = normalize_text(
        news.get(
            "url"
        )
    )

    published = normalize_text(
        news.get(
            "published_at"
        )
    )

    raw = "|".join(
        [
            source,
            title,
            url,
            published,
        ]
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


# =========================================================
# CACHE DIRECTORY
# =========================================================

def ensure_cache_directory(
    filepath: str,
) -> None:

    directory = os.path.dirname(
        filepath
    )

    if not directory:
        return

    try:

        os.makedirs(
            directory,
            exist_ok=True,
        )

    except Exception:

        logger.exception(
            "Gagal membuat directory cache: %s",
            directory,
        )


# =========================================================
# LOAD CACHE
# =========================================================

def load_cache(
    filepath: str,
) -> List[str]:

    if not filepath:
        return []

    if not os.path.exists(
        filepath
    ):

        return []

    try:

        with open(
            filepath,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            list,
        ):

            return [
                str(item)
                for item in data
                if item
            ]

        if isinstance(
            data,
            dict,
        ):

            items = data.get(
                "items",
                []
            )

            if isinstance(
                items,
                list,
            ):

                return [
                    str(item)
                    for item in items
                    if item
                ]

    except Exception:

        logger.exception(
            "Gagal membaca news cache: %s",
            filepath,
        )

    return []


# =========================================================
# SAVE CACHE
# =========================================================

def save_cache(
    filepath: str,
    items: List[str],
) -> bool:

    if not filepath:
        return False

    try:

        ensure_cache_directory(
            filepath
        )

        clean_items = list(
            dict.fromkeys(
                [
                    str(item)
                    for item in items
                    if item
                ]
            )
        )

        clean_items = clean_items[
            -MAX_CACHE_ITEMS:
        ]

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                clean_items,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return True

    except Exception:

        logger.exception(
            "Gagal menyimpan news cache: %s",
            filepath,
        )

        return False


# =========================================================
# CHECK DUPLICATE
# =========================================================

def is_duplicate_news(
    news_id: str,
    cache_file: str,
) -> bool:

    if not NEWS_PREVENT_DUPLICATE:
        return False

    cache = load_cache(
        cache_file
    )

    return news_id in cache


# =========================================================
# MARK NEWS AS SENT
# =========================================================

def mark_news_as_sent(
    news_id: str,
    cache_file: str,
) -> bool:

    if not NEWS_PREVENT_DUPLICATE:
        return True

    cache = load_cache(
        cache_file
    )

    if news_id not in cache:

        cache.append(
            news_id
        )

    return save_cache(
        cache_file,
        cache,
    )


# =========================================================
# NORMALIZE PROVIDER ARTICLE
# =========================================================

def normalize_article(
    article: Dict[str, Any],
) -> Optional[Dict[str, Any]]:

    if not isinstance(
        article,
        dict,
    ):

        return None

    # ---------------------------------------------
    # TITLE
    # ---------------------------------------------

    title = (
        article.get("title")
        or article.get("headline")
        or article.get("name")
        or ""
    )

    title = normalize_text(
        title
    )

    if not title:
        return None

    # ---------------------------------------------
    # DESCRIPTION
    # ---------------------------------------------

    description = (
        article.get("description")
        or article.get("summary")
        or article.get("snippet")
        or ""
    )

    description = normalize_text(
        description
    )

    # ---------------------------------------------
    # CONTENT
    # ---------------------------------------------

    content = (
        article.get("content")
        or article.get("body")
        or article.get("text")
        or ""
    )

    content = normalize_text(
        content
    )

    # ---------------------------------------------
    # URL
    # ---------------------------------------------

    url = (
        article.get("url")
        or article.get("link")
        or article.get("article_url")
        or ""
    )

    url = normalize_text(
        url
    )

    # ---------------------------------------------
    # SOURCE
    # ---------------------------------------------

    source_value = (
        article.get("source")
        or article.get("publisher")
        or article.get("site")
        or ""
    )

    if isinstance(
        source_value,
        dict,
    ):

        source = (
            source_value.get("name")
            or source_value.get("title")
            or ""
        )

    else:

        source = source_value

    source = normalize_text(
        source
    )

    # ---------------------------------------------
    # PUBLISHED TIME
    # ---------------------------------------------

    published_at = (
        article.get("published_at")
        or article.get("publishedAt")
        or article.get("published")
        or article.get("pubDate")
        or article.get("datetime")
        or article.get("date")
        or ""
    )

    published_at = normalize_text(
        published_at
    )

    # ---------------------------------------------
    # IMAGE
    # ---------------------------------------------

    image_url = (
        article.get("image")
        or article.get("image_url")
        or article.get("urlToImage")
        or ""
    )

    image_url = normalize_text(
        image_url
    )

    # ---------------------------------------------
    # CATEGORY
    # ---------------------------------------------

    category = (
        article.get("category")
        or article.get("section")
        or "markets"
    )

    category = normalize_text(
        category
    )

    normalized = {

        "title": title,

        "description": description,

        "content": content,

        "url": url,

        "source": source,

        "published_at": published_at,

        "published_at_wib": format_datetime_wib(
            published_at
        ),

        "image_url": image_url,

        "category": category,

    }

    # ---------------------------------------------
    # NEWS ID
    # ---------------------------------------------

    normalized[
        "news_id"
    ] = generate_news_id(
        normalized
    )

    return normalized


# =========================================================
# EXTRACT ARTICLES
# =========================================================

def extract_articles(
    payload: Any,
) -> List[Dict[str, Any]]:

    if not isinstance(
        payload,
        dict,
    ):

        return []

    # ---------------------------------------------
    # COMMON API FORMAT
    # ---------------------------------------------

    possible_keys = [

        "articles",

        "data",

        "results",

        "news",

        "items",

    ]

    for key in possible_keys:

        value = payload.get(
            key
        )

        if isinstance(
            value,
            list,
        ):

            return [
                item
                for item in value
                if isinstance(
                    item,
                    dict
                )
            ]

    # ---------------------------------------------
    # DATA DICT
    # ---------------------------------------------

    data = payload.get(
        "data"
    )

    if isinstance(
        data,
        dict,
    ):

        for key in possible_keys:

            value = data.get(
                key
            )

            if isinstance(
                value,
                list,
            ):

                return [
                    item
                    for item in value
                    if isinstance(
                        item,
                        dict
                    )
                ]

    return []


# =========================================================
# API REQUEST
# =========================================================

def request_news_api(
    limit: int = DEFAULT_NEWS_LIMIT,
) -> List[Dict[str, Any]]:

    if not NEWS_API_URL:

        logger.warning(
            "NEWS_API_URL belum diisi."
        )

        return []

    if not NEWS_API_KEY:

        logger.warning(
            "NEWS_API_KEY belum diisi."
        )

        return []

    limit = max(
        1,
        min(
            int(limit),
            100,
        )
    )

    # =====================================================
    # PARAMETER
    # =====================================================

    params = {

        "apiKey": NEWS_API_KEY,

        "q": "gold OR XAUUSD",

        "language": NEWS_SOURCE_LANGUAGE,

        "limit": limit,

    }

    try:

        logger.info(
            "Mengambil berita XAUUSD | limit=%s",
            limit,
        )

        response = _http_session.get(

            NEWS_API_URL,

            params=params,

            timeout=NEWS_REQUEST_TIMEOUT,

        )

        response.raise_for_status()

        payload = response.json()

        articles = extract_articles(
            payload
        )

        logger.info(
            "News API mengembalikan %s artikel.",
            len(articles),
        )

        return articles

    except requests.RequestException as exc:

        logger.error(
            "News API request error: %s",
            exc,
        )

    except ValueError as exc:

        logger.error(
            "News API JSON error: %s",
            exc,
        )

    except Exception:

        logger.exception(
            "Unexpected error saat mengambil berita."
        )

    return []


# =========================================================
# VALIDATE ARTICLE
# =========================================================

def validate_article(
    article: Dict[str, Any],
) -> bool:

    title = article.get(
        "title",
        ""
    )

    description = article.get(
        "description",
        ""
    )

    content = article.get(
        "content",
        ""
    )

    source = article.get(
        "source",
        ""
    )

    url = article.get(
        "url",
        ""
    )

    published_at = article.get(
        "published_at",
        ""
    )

    # ---------------------------------------------
    # TITLE
    # ---------------------------------------------

    if not title:
        return False

    # ---------------------------------------------
    # SOURCE
    # ---------------------------------------------

    if (
        NEWS_REQUIRE_SOURCE
        and not source
    ):

        logger.debug(
            "Artikel ditolak: source kosong."
        )

        return False

    # ---------------------------------------------
    # URL
    # ---------------------------------------------

    if (
        NEWS_REQUIRE_URL
        and not is_valid_url(
            url
        )
    ):

        logger.debug(
            "Artikel ditolak: URL tidak valid | %s",
            title,
        )

        return False

    # ---------------------------------------------
    # PUBLISHED DATE
    # ---------------------------------------------

    age = news_age_minutes(
        published_at
    )

    if age is None:

        logger.debug(
            "Artikel ditolak: waktu publikasi tidak valid | %s",
            title,
        )

        return False

    # Berita masa depan mencurigakan.
    if age < -5:

        logger.debug(
            "Artikel ditolak: tanggal publikasi masa depan | %s",
            title,
        )

        return False

    # ---------------------------------------------
    # MAX AGE
    # ---------------------------------------------

    max_age = NEWS_MAX_AGE_MINUTES

    if (
        age > max_age
    ):

        logger.debug(
            "Artikel terlalu lama | age=%.1f min | title=%s",
            age,
            title,
        )

        return False

    # ---------------------------------------------
    # BLOCKED
    # ---------------------------------------------

    if is_blocked_news(
        title,
        description,
        content,
    ):

        return False

    # ---------------------------------------------
    # RELEVANCE
    # ---------------------------------------------

    if not is_relevant_news(
        title,
        description,
        content,
    ):

        logger.debug(
            "Artikel tidak relevan dengan XAUUSD | %s",
            title,
        )

        return False

    return True


# =========================================================
# SCORE ARTICLE
# =========================================================

def score_article(
    article: Dict[str, Any],
) -> float:

    title = article.get(
        "title",
        ""
    )

    description = article.get(
        "description",
        ""
    )

    content = article.get(
        "content",
        ""
    )

    source = article.get(
        "source",
        ""
    )

    published_at = article.get(
        "published_at",
        ""
    )

    text = " ".join(
        [
            title,
            description,
            content,
        ]
    )

    # ---------------------------------------------
    # SOURCE SCORE
    # ---------------------------------------------

    score = float(
        source_score(
            source
        )
    )

    # ---------------------------------------------
    # KEYWORD SCORE
    # ---------------------------------------------

    matches = keyword_match(
        text,
        FUNDAMENTAL_SEARCH_KEYWORDS,
    )

    score += min(
        len(matches) * 8,
        40,
    )

    # ---------------------------------------------
    # GOLD DIRECT SCORE
    # ---------------------------------------------

    gold_matches = keyword_match(
        text,
        [
            "gold",
            "XAUUSD",
            "XAU/USD",
            "gold price",
        ],
    )

    score += min(
        len(gold_matches) * 10,
        30,
    )

    # ---------------------------------------------
    # FRESHNESS
    # ---------------------------------------------

    age = news_age_minutes(
        published_at
    )

    if age is not None:

        if age <= 15:
            score += 30

        elif age <= 30:
            score += 25

        elif age <= 60:
            score += 20

        elif age <= 120:
            score += 10

        elif age <= 180:
            score += 5

    return score


# =========================================================
# FILTER ARTICLES
# =========================================================

def filter_articles(
    raw_articles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    valid = []

    seen = set()

    for raw_article in raw_articles:

        article = normalize_article(
            raw_article
        )

        if article is None:
            continue

        news_id = article.get(
            "news_id"
        )

        # ---------------------------------------------
        # DUPLICATE DALAM RESPONSE
        # ---------------------------------------------

        if news_id in seen:

            continue

        seen.add(
            news_id
        )

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------

        if not validate_article(
            article
        ):

            continue

        # ---------------------------------------------
        # SCORE
        # ---------------------------------------------

        article[
            "score"
        ] = score_article(
            article
        )

        valid.append(
            article
        )

    # ---------------------------------------------
    # SORT
    # ---------------------------------------------

    valid.sort(
        key=lambda item: (
            item.get(
                "score",
                0
            ),
            -(
                news_age_minutes(
                    item.get(
                        "published_at"
                    )
                )
                or 999999
            ),
        ),
        reverse=True,
    )

    return valid


# =========================================================
# FETCH LATEST NEWS
# =========================================================

def fetch_latest_news(
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:

    if limit is None:

        limit = NEWS_FETCH_LIMIT

    raw_articles = request_news_api(
        limit=limit
    )

    if not raw_articles:

        logger.warning(
            "Tidak ada raw news dari provider."
        )

        return []

    articles = filter_articles(
        raw_articles
    )

    logger.info(
        "Berita valid setelah filter: %s",
        len(articles),
    )

    return articles


# =========================================================
# GET BEST NEWS
# =========================================================

def get_latest_news(
    cache_file: Optional[str] = None,
) -> Optional[Dict[str, Any]]:

    if cache_file is None:

        cache_file = (
            FUNDAMENTAL_NEWS_CACHE_FILE
        )

    articles = fetch_latest_news(
        limit=NEWS_FETCH_LIMIT
    )

    if not articles:

        logger.warning(
            "Tidak ditemukan berita XAUUSD yang valid."
        )

        return None

    # =====================================================
    # CARI BERITA YANG BELUM PERNAH DIKIRIM
    # =====================================================

    for article in articles:

        news_id = article.get(
            "news_id"
        )

        if not news_id:
            continue

        if is_duplicate_news(
            news_id,
            cache_file,
        ):

            logger.debug(
                "Berita duplicate dilewati | %s",
                article.get(
                    "title"
                ),
            )

            continue

        logger.info(
            "Berita terbaik ditemukan | "
            "score=%.1f | source=%s | title=%s",
            article.get(
                "score",
                0
            ),
            article.get(
                "source"
            ),
            article.get(
                "title"
            ),
        )

        return article

    logger.info(
        "Semua berita kandidat sudah pernah digunakan."
    )

    return None


# =========================================================
# GET FUNDAMENTAL NEWS
# =========================================================

def get_fundamental_news() -> Optional[Dict[str, Any]]:

    """
    Mengambil 1 berita terbaru untuk Fundamental AI.

    Tidak menentukan BUY / SELL.
    """

    logger.info(
        "Mencari berita FUNDAMENTAL terbaru..."
    )

    news = get_latest_news(
        cache_file=(
            FUNDAMENTAL_NEWS_CACHE_FILE
        )
    )

    if news is None:

        logger.info(
            "Tidak ada berita fundamental baru."
        )

        return None

    news[
        "mode"
    ] = "fundamental"

    return news


# =========================================================
# GET COMBINED NEWS
# =========================================================

def get_combined_news() -> Optional[Dict[str, Any]]:

    """
    Mengambil 1 berita terbaru untuk Combined AI.

    Combined AI nantinya menggabungkan:

        Fundamental
              +
        SMC

    Fungsi ini hanya menyediakan berita.
    """

    logger.info(
        "Mencari berita untuk COMBINED AI..."
    )

    news = get_latest_news(
        cache_file=(
            COMBINED_NEWS_CACHE_FILE
        )
    )

    if news is None:

        logger.info(
            "Tidak ada berita combined baru."
        )

        return None

    news[
        "mode"
    ] = "combined"

    return news


# =========================================================
# MARK FUNDAMENTAL SENT
# =========================================================

def mark_fundamental_sent(
    news: Dict[str, Any],
) -> bool:

    if not news:
        return False

    news_id = news.get(
        "news_id"
    )

    if not news_id:
        return False

    return mark_news_as_sent(
        news_id,
        FUNDAMENTAL_NEWS_CACHE_FILE,
    )


# =========================================================
# MARK COMBINED SENT
# =========================================================

def mark_combined_sent(
    news: Dict[str, Any],
) -> bool:

    if not news:
        return False

    news_id = news.get(
        "news_id"
    )

    if not news_id:
        return False

    return mark_news_as_sent(
        news_id,
        COMBINED_NEWS_CACHE_FILE,
    )


# =========================================================
# NEWS SUMMARY DATA
# =========================================================

def build_news_context(
    news: Dict[str, Any],
) -> Dict[str, Any]:

    if not news:

        return {

            "available": False,

            "title": "",

            "source": "",

            "url": "",

            "published_at": "",

            "published_at_wib": "",

            "description": "",

            "content": "",

            "score": 0,

        }

    return {

        "available": True,

        "news_id": news.get(
            "news_id",
            "",
        ),

        "title": news.get(
            "title",
            "",
        ),

        "source": news.get(
            "source",
            "",
        ),

        "url": news.get(
            "url",
            "",
        ),

        "published_at": news.get(
            "published_at",
            "",
        ),

        "published_at_wib": news.get(
            "published_at_wib",
            "",
        ),

        "description": news.get(
            "description",
            "",
        ),

        "content": news.get(
            "content",
            "",
        ),

        "score": news.get(
            "score",
            0,
        ),

    }


# =========================================================
# NEWS TELEGRAM FORMAT
# =========================================================

def format_news_for_telegram(
    news: Dict[str, Any],
) -> str:

    if not news:

        return (
            "📰 *FUNDAMENTAL NEWS*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Tidak ada berita fundamental valid."
        )

    title = normalize_text(
        news.get(
            "title"
        )
    )

    source = normalize_text(
        news.get(
            "source"
        )
    )

    published = normalize_text(
        news.get(
            "published_at_wib"
        )
    )

    description = normalize_text(
        news.get(
            "description"
        )
    )

    url = normalize_text(
        news.get(
            "url"
        )
    )

    text = (
        "📰 *XAU FUNDAMENTAL NEWS*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"📌 *{title}*\n\n"
        f"🏦 Sumber: *{source or '-'}*\n"
        f"🕒 Waktu: *{published or '-'}*\n\n"
    )

    if description:

        text += (
            f"📝 {description}\n\n"
        )

    if url:

        text += (
            f"🔗 [Baca Artikel Asli]({url})"
        )

    return text


# =========================================================
# NEWS STATUS
# =========================================================

def get_news_status() -> Dict[str, Any]:

    return {

        "api_configured": bool(
            NEWS_API_KEY
        ),

        "url_configured": bool(
            NEWS_API_URL
        ),

        "source_language": (
            NEWS_SOURCE_LANGUAGE
        ),

        "output_language": (
            NEWS_OUTPUT_LANGUAGE
        ),

        "fetch_limit": (
            NEWS_FETCH_LIMIT
        ),

        "max_age_minutes": (
            NEWS_MAX_AGE_MINUTES
        ),

        "request_timeout": (
            NEWS_REQUEST_TIMEOUT
        ),

        "fundamental_cache": (
            FUNDAMENTAL_NEWS_CACHE_FILE
        ),

        "combined_cache": (
            COMBINED_NEWS_CACHE_FILE
        ),

    }


# =========================================================
# TEST CONNECTION
# =========================================================

def test_news_connection() -> Dict[str, Any]:

    status = get_news_status()

    if not status[
        "api_configured"
    ]:

        return {

            "success": False,

            "error": (
                "NEWS_API_KEY belum diisi."
            ),

        }

    if not status[
        "url_configured"
    ]:

        return {

            "success": False,

            "error": (
                "NEWS_API_URL belum diisi."
            ),

        }

    try:

        articles = request_news_api(
            limit=1
        )

        return {

            "success": bool(
                articles
            ),

            "articles": len(
                articles
            ),

        }

    except Exception as exc:

        logger.exception(
            "News connection test gagal."
        )

        return {

            "success": False,

            "error": str(
                exc
            ),

        }


# =========================================================
# MODULE LOAD LOG
# =========================================================

logger.info(
    "News Service loaded | "
    "API configured=%s | "
    "URL configured=%s | "
    "fetch_limit=%s | "
    "max_age=%s minutes",
    bool(
        NEWS_API_KEY
    ),
    bool(
        NEWS_API_URL
    ),
    NEWS_FETCH_LIMIT,
    NEWS_MAX_AGE_MINUTES,
)
