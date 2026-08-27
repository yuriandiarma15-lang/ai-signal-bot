"""
services/fundamental.py

XAU AI SIGNAL BOT
=================

FUNDAMENTAL NEWS SERVICE

Fungsi:
- Mengambil berita fundamental terbaru
- Fokus XAUUSD / Gold
- Filter berita yang relevan
- Filter berita terlarang
- Validasi umur berita
- Validasi source
- Validasi URL
- Mencegah duplicate news
- Menyediakan data untuk:
    1. Fundamental News
    2. Combined AI

CATATAN:
- Tidak mengubah logic SMC.
- Tidak membuat Entry / TP / SL.
- Fundamental hanya memberikan konteks berita.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from config.settings import (
    NEWS_API_KEY,
    NEWS_API_URL,
    NEWS_FETCH_LIMIT,
    NEWS_KEYWORDS,
    NEWS_MAX_AGE_MINUTES,
    NEWS_REQUIRE_SOURCE,
    NEWS_REQUIRE_URL,
    NEWS_PREVENT_DUPLICATE,
    FUNDAMENTAL_SEARCH_KEYWORDS,
    FUNDAMENTAL_BLOCKED_KEYWORDS,
    FUNDAMENTAL_MAX_NEWS_AGE_HOURS,
    FUNDAMENTAL_NEWS_PER_UPDATE,
    FUNDAMENTAL_NEWS_CACHE_FILE,
    FUNDAMENTAL_SOURCE_PRIORITY,
    FUNDAMENTAL_LANGUAGE,
    NEWS_REQUEST_TIMEOUT,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

DEFAULT_NEWS_API_URL = (
    "https://newsapi.org/v2/everything"
)


# =========================================================
# HELPERS
# =========================================================

def _ensure_cache_directory():
    """
    Membuat folder cache jika belum tersedia.
    """

    path = FUNDAMENTAL_NEWS_CACHE_FILE

    directory = os.path.dirname(path)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )


def _load_cache() -> List[str]:
    """
    Membaca ID berita yang sudah pernah dikirim.
    """

    try:

        _ensure_cache_directory()

        if not os.path.exists(
            FUNDAMENTAL_NEWS_CACHE_FILE
        ):
            return []

        with open(
            FUNDAMENTAL_NEWS_CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):

            values = data.get(
                "items",
                []
            )

            if isinstance(
                values,
                list
            ):
                return values

        return []

    except Exception:

        logger.exception(
            "Gagal membaca fundamental news cache."
        )

        return []


def _save_cache(
    cache: List[str]
):
    """
    Menyimpan cache berita.
    """

    try:

        _ensure_cache_directory()

        # Batasi ukuran cache.
        cache = cache[-500:]

        with open(
            FUNDAMENTAL_NEWS_CACHE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                {
                    "items": cache,
                    "updated_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
                file,
                ensure_ascii=False,
                indent=2,
            )

    except Exception:

        logger.exception(
            "Gagal menyimpan fundamental news cache."
        )


def _normalize_text(
    value: Any
) -> str:
    """
    Normalisasi text.
    """

    if value is None:
        return ""

    return str(
        value
    ).strip()


def _contains_keyword(
    text: str,
    keywords: List[str],
) -> bool:
    """
    Mengecek apakah text mengandung keyword.
    """

    text_lower = text.lower()

    for keyword in keywords:

        keyword = _normalize_text(
            keyword
        )

        if not keyword:
            continue

        if keyword.lower() in text_lower:
            return True

    return False


def _contains_blocked_keyword(
    text: str,
) -> bool:
    """
    Mengecek berita yang harus diblokir.

    Contoh:
    FOMC
    NFP
    PPI
    CPI
    """

    return _contains_keyword(
        text,
        FUNDAMENTAL_BLOCKED_KEYWORDS,
    )


def _parse_datetime(
    value: Any
) -> Optional[datetime]:
    """
    Mengubah berbagai format datetime menjadi
    timezone-aware UTC.
    """

    if not value:
        return None

    value = str(
        value
    ).strip()

    try:

        # ISO format.
        dt = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00"
            )
        )

        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=timezone.utc
            )

        return dt.astimezone(
            timezone.utc
        )

    except Exception:
        pass

    # Format umum lainnya.
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt,
            )

            return dt.replace(
                tzinfo=timezone.utc
            )

        except Exception:
            continue

    return None


def _news_age_minutes(
    published_at: Any
) -> Optional[float]:
    """
    Menghitung umur berita dalam menit.
    """

    dt = _parse_datetime(
        published_at
    )

    if dt is None:
        return None

    now = datetime.now(
        timezone.utc
    )

    age = (
        now - dt
    ).total_seconds() / 60

    return age


def _make_news_id(
    title: str,
    url: str,
) -> str:
    """
    Membuat ID stabil untuk duplicate protection.
    """

    raw = (
        f"{title.strip()}|{url.strip()}"
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()


def _source_name(
    article: Dict[str, Any]
) -> str:
    """
    Mengambil nama publisher.
    """

    source = article.get(
        "source"
    )

    if isinstance(
        source,
        dict
    ):

        return _normalize_text(
            source.get(
                "name"
            )
        )

    return _normalize_text(
        article.get(
            "publisher"
        )
    )


def _article_url(
    article: Dict[str, Any]
) -> str:
    """
    Mengambil URL artikel asli.
    """

    return _normalize_text(
        article.get(
            "url"
        )
    )


def _article_title(
    article: Dict[str, Any]
) -> str:
    """
    Mengambil judul artikel.
    """

    return _normalize_text(
        article.get(
            "title"
        )
    )


def _article_description(
    article: Dict[str, Any]
) -> str:
    """
    Mengambil description.
    """

    return _normalize_text(
        article.get(
            "description"
        )
    )


def _article_content(
    article: Dict[str, Any]
) -> str:
    """
    Mengambil content.
    """

    return _normalize_text(
        article.get(
            "content"
        )
    )


# =========================================================
# SOURCE SCORE
# =========================================================

def _source_priority_score(
    source: str
) -> int:
    """
    Semakin tinggi semakin prioritas.
    """

    source_lower = source.lower()

    for index, preferred in enumerate(
        FUNDAMENTAL_SOURCE_PRIORITY
    ):

        if preferred.lower() in source_lower:

            # Sumber pertama = score terbesar.
            return (
                len(FUNDAMENTAL_SOURCE_PRIORITY)
                - index
            )

    return 0


# =========================================================
# VALIDATE ARTICLE
# =========================================================

def validate_article(
    article: Dict[str, Any],
) -> bool:
    """
    Validasi dasar artikel.
    """

    if not isinstance(
        article,
        dict
    ):
        return False


    title = _article_title(
        article
    )

    source = _source_name(
        article
    )

    url = _article_url(
        article
    )

    description = _article_description(
        article
    )

    content = _article_content(
        article
    )


    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    if not title:

        logger.debug(
            "Artikel ditolak: title kosong."
        )

        return False


    # -----------------------------------------------------
    # SOURCE
    # -----------------------------------------------------

    if (
        NEWS_REQUIRE_SOURCE
        and not source
    ):

        logger.debug(
            "Artikel ditolak: source kosong."
        )

        return False


    # -----------------------------------------------------
    # URL
    # -----------------------------------------------------

    if (
        NEWS_REQUIRE_URL
        and not url
    ):

        logger.debug(
            "Artikel ditolak: URL kosong."
        )

        return False


    # -----------------------------------------------------
    # CONTENT
    # -----------------------------------------------------

    combined_text = " ".join(
        [
            title,
            description,
            content,
        ]
    )


    # -----------------------------------------------------
    # BLOCKED KEYWORD
    # -----------------------------------------------------

    if _contains_blocked_keyword(
        combined_text
    ):

        logger.info(
            "Artikel diblokir | title=%s",
            title,
        )

        return False


    # -----------------------------------------------------
    # XAU / FUNDAMENTAL RELEVANCE
    # -----------------------------------------------------

    relevant = (
        _contains_keyword(
            combined_text,
            FUNDAMENTAL_SEARCH_KEYWORDS,
        )
        or
        _contains_keyword(
            combined_text,
            NEWS_KEYWORDS,
        )
    )

    if not relevant:

        logger.debug(
            "Artikel tidak relevan dengan Gold | "
            "title=%s",
            title,
        )

        return False


    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    published_at = article.get(
        "publishedAt"
    )

    age_minutes = _news_age_minutes(
        published_at
    )


    if age_minutes is not None:

        # Gunakan batas setting fundamental
        # jika tersedia.

        max_age_minutes = (
            FUNDAMENTAL_MAX_NEWS_AGE_HOURS
            * 60
        )

        # NEWS_MAX_AGE_MINUTES juga dipakai
        # sebagai batas umum.

        if (
            max_age_minutes
            and age_minutes
            > max_age_minutes
        ):

            logger.debug(
                "Artikel terlalu lama | "
                "age=%.1f menit | title=%s",
                age_minutes,
                title,
            )

            return False

        if (
            NEWS_MAX_AGE_MINUTES
            and age_minutes
            > NEWS_MAX_AGE_MINUTES
        ):

            logger.debug(
                "Artikel melewati NEWS_MAX_AGE_MINUTES | "
                "age=%.1f | title=%s",
                age_minutes,
                title,
            )

            return False


    return True


# =========================================================
# FETCH NEWS
# =========================================================

def fetch_news(
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Mengambil kandidat berita dari News API.

    Return:
        list artikel mentah yang sudah lolos
        validasi dasar.
    """

    if limit is None:

        limit = NEWS_FETCH_LIMIT


    # -----------------------------------------------------
    # API KEY
    # -----------------------------------------------------

    if not NEWS_API_KEY:

        logger.error(
            "NEWS_API_KEY belum diisi."
        )

        return []


    # -----------------------------------------------------
    # API URL
    # -----------------------------------------------------

    api_url = (
        NEWS_API_URL
        or DEFAULT_NEWS_API_URL
    )


    # -----------------------------------------------------
    # QUERY
    # -----------------------------------------------------

    query_parts = []

    for keyword in FUNDAMENTAL_SEARCH_KEYWORDS:

        keyword = _normalize_text(
            keyword
        )

        if keyword:
            query_parts.append(
                f'"{keyword}"'
            )


    query = " OR ".join(
        query_parts
    )


    # -----------------------------------------------------
    # PARAMETER
    # -----------------------------------------------------

    params = {

        "apiKey": NEWS_API_KEY,

        "q": query,

        "language": "en",

        "sortBy": "publishedAt",

        "pageSize": max(
            1,
            int(limit)
        ),

    }


    # -----------------------------------------------------
    # REQUEST
    # -----------------------------------------------------

    try:

        logger.info(
            "Mengambil berita fundamental | "
            "limit=%s",
            limit,
        )

        response = requests.get(

            api_url,

            params=params,

            timeout=NEWS_REQUEST_TIMEOUT,

        )


        response.raise_for_status()


        data = response.json()


    except requests.RequestException:

        logger.exception(
            "Request fundamental news gagal."
        )

        return []


    except Exception:

        logger.exception(
            "Error membaca response fundamental news."
        )

        return []


    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = data.get(
        "status"
    )

    if status != "ok":

        logger.error(
            "News API error | response=%s",
            data,
        )

        return []


    # -----------------------------------------------------
    # ARTICLES
    # -----------------------------------------------------

    articles = data.get(
        "articles",
        []
    )


    if not isinstance(
        articles,
        list
    ):

        logger.error(
            "Format articles tidak valid."
        )

        return []


    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    valid_articles = []


    for article in articles:

        if validate_article(
            article
        ):

            valid_articles.append(
                article
            )


    logger.info(
        "Fundamental news | "
        "raw=%s | valid=%s",
        len(articles),
        len(valid_articles),
    )


    return valid_articles


# =========================================================
# SORT NEWS
# =========================================================

def sort_news(
    articles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Mengurutkan berita:

    1. Source prioritas
    2. Berita terbaru
    """

    def sort_key(
        article
    ):

        source = _source_name(
            article
        )

        published_at = _parse_datetime(
            article.get(
                "publishedAt"
            )
        )

        timestamp = (
            published_at.timestamp()
            if published_at
            else 0
        )

        source_score = (
            _source_priority_score(
                source
            )
        )

        return (
            source_score,
            timestamp,
        )

    return sorted(
        articles,
        key=sort_key,
        reverse=True,
    )


# =========================================================
# FORMAT NEWS
# =========================================================

def normalize_article(
    article: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mengubah artikel mentah menjadi format internal.
    """

    title = _article_title(
        article
    )

    source = _source_name(
        article
    )

    url = _article_url(
        article
    )

    description = _article_description(
        article
    )

    content = _article_content(
        article
    )

    published_at = _normalize_text(
        article.get(
            "publishedAt"
        )
    )


    news_id = _make_news_id(
        title,
        url,
    )


    return {

        "id": news_id,

        "title": title,

        "source": source,

        "url": url,

        "published_at": published_at,

        "description": description,

        "content": content,

        "language": FUNDAMENTAL_LANGUAGE,

        "topic": "XAUUSD",

    }


# =========================================================
# GET LATEST NEWS
# =========================================================

def get_latest_news(
    count: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Mengambil berita fundamental terbaru.

    Duplicate news akan dilewati.
    """

    if count is None:

        count = FUNDAMENTAL_NEWS_PER_UPDATE


    articles = fetch_news(
        limit=NEWS_FETCH_LIMIT
    )


    if not articles:

        logger.warning(
            "Tidak ada berita fundamental valid."
        )

        return []


    articles = sort_news(
        articles
    )


    cache = _load_cache()

    cache_set = set(
        cache
    )


    result = []


    for article in articles:

        normalized = normalize_article(
            article
        )

        news_id = normalized.get(
            "id"
        )


        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        if (
            NEWS_PREVENT_DUPLICATE
            and news_id in cache_set
        ):

            logger.debug(
                "News duplicate dilewati | "
                "title=%s",
                normalized.get(
                    "title"
                ),
            )

            continue


        result.append(
            normalized
        )


        if len(result) >= count:

            break


    logger.info(
        "Berita fundamental terpilih | count=%s",
        len(result),
    )


    return result


# =========================================================
# GET ONE LATEST NEWS
# =========================================================

def get_latest_news_item() -> Optional[
    Dict[str, Any]
]:
    """
    Mengambil 1 berita terbaru.
    """

    items = get_latest_news(
        count=1
    )

    if not items:
        return None

    return items[0]


# =========================================================
# MARK AS SENT
# =========================================================

def mark_news_as_sent(
    news_id: str
) -> bool:
    """
    Menandai berita sebagai sudah dikirim.
    """

    if not news_id:

        return False


    try:

        cache = _load_cache()

        if news_id not in cache:

            cache.append(
                news_id
            )


        _save_cache(
            cache
        )


        logger.info(
            "News ditandai sebagai sent | id=%s",
            news_id,
        )

        return True


    except Exception:

        logger.exception(
            "Gagal menandai news sebagai sent."
        )

        return False


# =========================================================
# MARK ARTICLE AS SENT
# =========================================================

def mark_article_as_sent(
    article: Dict[str, Any]
) -> bool:
    """
    Menandai article sebagai sudah dikirim.
    """

    normalized = normalize_article(
        article
    )

    return mark_news_as_sent(
        normalized.get(
            "id"
        )
    )


# =========================================================
# CLEAR CACHE
# =========================================================

def clear_news_cache():
    """
    Menghapus cache duplicate.
    """

    try:

        _ensure_cache_directory()

        with open(
            FUNDAMENTAL_NEWS_CACHE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                {
                    "items": [],
                    "updated_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
                file,
                ensure_ascii=False,
                indent=2,
            )


        logger.info(
            "Fundamental news cache dibersihkan."
        )


    except Exception:

        logger.exception(
            "Gagal membersihkan news cache."
        )


# =========================================================
# NEWS SUMMARY DATA
# =========================================================

def build_fundamental_context(
    news: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Membuat context fundamental yang nantinya
    dapat digunakan Combined AI.

    Tidak membuat keputusan trading.
    """

    if not news:

        return {

            "available": False,

            "title": "",

            "source": "",

            "url": "",

            "published_at": "",

            "summary": "",

            "impact": "UNKNOWN",

        }


    title = news.get(
        "title",
        ""
    )

    description = news.get(
        "description",
        ""
    )

    content = news.get(
        "content",
        ""
    )


    text = " ".join(
        [
            title,
            description,
            content,
        ]
    ).strip()


    return {

        "available": True,

        "id": news.get(
            "id",
            "",
        ),

        "title": title,

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

        "summary": text,

        "impact": "UNKNOWN",

        "language": FUNDAMENTAL_LANGUAGE,

        "topic": "XAUUSD",

    }


# =========================================================
# PUBLIC SERVICE
# =========================================================

class FundamentalService:
    """
    Wrapper service untuk scheduler / handler.
    """

    def __init__(self):

        self.enabled = True


    def latest(
        self,
        count: int = 1,
    ) -> List[Dict[str, Any]]:

        return get_latest_news(
            count=count
        )


    def latest_one(
        self,
    ) -> Optional[Dict[str, Any]]:

        return get_latest_news_item()


    def context(
        self,
        news: Optional[
            Dict[str, Any]
        ],
    ) -> Dict[str, Any]:

        return build_fundamental_context(
            news
        )


    def mark_sent(
        self,
        news_id: str,
    ) -> bool:

        return mark_news_as_sent(
            news_id
        )


# =========================================================
# SINGLETON
# =========================================================

fundamental_service = FundamentalService()
