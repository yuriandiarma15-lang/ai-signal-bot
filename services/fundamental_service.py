"""
services/fundamental_service.py

XAU AI SIGNAL BOT
FUNDAMENTAL NEWS SERVICE
========================

Fungsi:
- Mengambil berita terbaru yang relevan dengan Gold/XAUUSD
- Memfilter berita yang tidak diinginkan
- Memprioritaskan sumber terpercaya
- Validasi umur berita
- Validasi source dan URL
- Mencegah berita duplicate
- Menyediakan 1 berita terbaik
- Menyediakan analisa dampak berita terhadap Gold
- Menyediakan data untuk Combined AI

CATATAN:
--------
File ini TIDAK mengubah logic SMC.

SMC tetap berada di:
    services/signal_builder.py
    services/smc_analyzer.py
    dan file SMC lainnya.

Fundamental hanya menjadi layer tambahan.
"""

import json
import logging
import os
import re

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests


from config.settings import (
    NEWS_API_KEY,
    NEWS_API_URL,

    NEWS_SOURCE_LANGUAGE,
    NEWS_OUTPUT_LANGUAGE,

    NEWS_MAX_AGE_MINUTES,
    NEWS_FETCH_LIMIT,

    NEWS_KEYWORDS,

    NEWS_REQUIRE_SOURCE,
    NEWS_REQUIRE_URL,

    NEWS_PREVENT_DUPLICATE,

    NEWS_TRANSLATE_TO_INDONESIAN,
    NEWS_ENABLE_SUMMARY,
    NEWS_ENABLE_GOLD_IMPACT,

    FUNDAMENTAL_ENABLED,
    FUNDAMENTAL_NEWS_PER_UPDATE,
    FUNDAMENTAL_MAX_NEWS_AGE_HOURS,

    FUNDAMENTAL_BLOCKED_KEYWORDS,
    FUNDAMENTAL_SEARCH_KEYWORDS,
    FUNDAMENTAL_SOURCE_PRIORITY,

    FUNDAMENTAL_LANGUAGE,

    FUNDAMENTAL_NEWS_CACHE_FILE,

    NEWS_REQUEST_TIMEOUT,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONSTANT
# =========================================================

UTC = timezone.utc


# =========================================================
# CACHE
# =========================================================

_CACHE_MEMORY: List[str] = []


# =========================================================
# TEXT NORMALIZER
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
# LOWER TEXT
# =========================================================

def lower_text(
    value: Any,
) -> str:

    return normalize_text(
        value
    ).lower()


# =========================================================
# ENSURE CACHE DIRECTORY
# =========================================================

def ensure_cache_directory() -> None:

    path = (
        FUNDAMENTAL_NEWS_CACHE_FILE
    )


    directory = os.path.dirname(
        path
    )


    if directory:

        os.makedirs(
            directory,
            exist_ok=True,
        )


# =========================================================
# LOAD CACHE
# =========================================================

def load_cache() -> List[str]:

    global _CACHE_MEMORY


    if _CACHE_MEMORY:

        return _CACHE_MEMORY


    path = (
        FUNDAMENTAL_NEWS_CACHE_FILE
    )


    try:

        if not os.path.exists(
            path
        ):

            _CACHE_MEMORY = []

            return []


        with open(
            path,
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

            _CACHE_MEMORY = [
                str(item)
                for item in data
                if item
            ]


        elif isinstance(
            data,
            dict,
        ):

            cached = data.get(
                "urls",
                []
            )


            if isinstance(
                cached,
                list,
            ):

                _CACHE_MEMORY = [
                    str(item)
                    for item in cached
                    if item
                ]

            else:

                _CACHE_MEMORY = []


        else:

            _CACHE_MEMORY = []


    except Exception:

        logger.exception(
            "Gagal membaca fundamental news cache."
        )

        _CACHE_MEMORY = []


    return _CACHE_MEMORY


# =========================================================
# SAVE CACHE
# =========================================================

def save_cache(
    cache: List[str],
) -> None:

    global _CACHE_MEMORY


    # =====================================================
    # HAPUS DUPLICATE
    # =====================================================

    unique = []

    seen = set()


    for item in cache:

        item = normalize_text(
            item
        )


        if not item:

            continue


        if item in seen:

            continue


        seen.add(
            item
        )

        unique.append(
            item
        )


    # =====================================================
    # BATASI CACHE
    # =====================================================

    unique = unique[
        -500:
    ]


    _CACHE_MEMORY = unique


    try:

        ensure_cache_directory()


        with open(
            FUNDAMENTAL_NEWS_CACHE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                unique,
                file,
                ensure_ascii=False,
                indent=2,
            )


    except Exception:

        logger.exception(
            "Gagal menyimpan fundamental news cache."
        )


# =========================================================
# MARK AS SEEN
# =========================================================

def mark_news_seen(
    news: Dict[str, Any],
) -> None:

    url = normalize_text(
        news.get(
            "url"
        )
    )


    if not url:

        return


    cache = load_cache()


    if url not in cache:

        cache.append(
            url
        )


        save_cache(
            cache
        )


# =========================================================
# IS NEWS SEEN
# =========================================================

def is_news_seen(
    news: Dict[str, Any],
) -> bool:

    url = normalize_text(
        news.get(
            "url"
        )
    )


    if not url:

        return False


    return url in load_cache()


# =========================================================
# VALID URL
# =========================================================

def is_valid_url(
    url: str,
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
# PARSE DATE
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


        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=UTC
            )


        return dt.astimezone(
            UTC
        )


    value = normalize_text(
        value
    )


    if not value:

        return None


    # =====================================================
    # ISO
    # =====================================================

    try:

        iso_value = value.replace(
            "Z",
            "+00:00",
        )


        dt = datetime.fromisoformat(
            iso_value
        )


        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=UTC
            )


        return dt.astimezone(
            UTC
        )


    except Exception:

        pass


    # =====================================================
    # COMMON FORMAT
    # =====================================================

    formats = [

        "%Y-%m-%dT%H:%M:%S.%fZ",

        "%Y-%m-%dT%H:%M:%SZ",

        "%Y-%m-%dT%H:%M:%S",

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%d %H:%M",

        "%a, %d %b %Y %H:%M:%S %z",

    ]


    for fmt in formats:

        try:

            dt = datetime.strptime(
                value,
                fmt,
            )


            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=UTC
                )


            return dt.astimezone(
                UTC
            )


        except Exception:

            continue


    return None


# =========================================================
# NEWS AGE
# =========================================================

def news_age_minutes(
    news: Dict[str, Any],
) -> Optional[float]:

    published_at = news.get(
        "published_at"
    )


    dt = parse_datetime(
        published_at
    )


    if dt is None:

        return None


    now = datetime.now(
        UTC
    )


    age = (
        now - dt
    ).total_seconds() / 60


    return age


# =========================================================
# NEWS TOO OLD
# =========================================================

def is_news_too_old(
    news: Dict[str, Any],
) -> bool:

    age = news_age_minutes(
        news
    )


    if age is None:

        return False


    # =====================================================
    # Gunakan setting Fundamental
    # =====================================================

    max_age = (
        FUNDAMENTAL_MAX_NEWS_AGE_HOURS
        * 60
    )


    # =====================================================
    # Jangan gunakan berita dari masa depan
    # =====================================================

    if age < -5:

        return True


    return age > max_age


# =========================================================
# BLOCKED KEYWORD
# =========================================================

def contains_blocked_keyword(
    news: Dict[str, Any],
) -> bool:

    title = lower_text(
        news.get(
            "title"
        )
    )


    description = lower_text(
        news.get(
            "description"
        )
    )


    content = lower_text(
        news.get(
            "content"
        )
    )


    combined = " ".join(
        [
            title,
            description,
            content,
        ]
    )


    for keyword in (
        FUNDAMENTAL_BLOCKED_KEYWORDS
    ):

        keyword = lower_text(
            keyword
        )


        if not keyword:

            continue


        # =================================================
        # Word boundary untuk keyword tertentu
        # =================================================

        if keyword in combined:

            return True


    return False


# =========================================================
# RELEVANT KEYWORD
# =========================================================

def contains_relevant_keyword(
    news: Dict[str, Any],
) -> bool:

    title = lower_text(
        news.get(
            "title"
        )
    )


    description = lower_text(
        news.get(
            "description"
        )
    )


    content = lower_text(
        news.get(
            "content"
        )
    )


    combined = " ".join(
        [
            title,
            description,
            content,
        ]
    )


    keywords = list(
        FUNDAMENTAL_SEARCH_KEYWORDS
    )


    # Tambahkan keyword lama
    keywords.extend(
        NEWS_KEYWORDS
    )


    for keyword in keywords:

        keyword = lower_text(
            keyword
        )


        if not keyword:

            continue


        if keyword in combined:

            return True


    return False


# =========================================================
# SOURCE SCORE
# =========================================================

def source_priority_score(
    source: str,
) -> int:

    source = lower_text(
        source
    )


    if not source:

        return 0


    for index, priority in enumerate(
        FUNDAMENTAL_SOURCE_PRIORITY
    ):

        priority = lower_text(
            priority
        )


        if priority in source:

            # Sumber pertama mendapat score tertinggi
            return (
                len(FUNDAMENTAL_SOURCE_PRIORITY)
                - index
            )


    return 1


# =========================================================
# RELEVANCE SCORE
# =========================================================

def relevance_score(
    news: Dict[str, Any],
) -> int:

    title = lower_text(
        news.get(
            "title"
        )
    )


    description = lower_text(
        news.get(
            "description"
        )
    )


    content = lower_text(
        news.get(
            "content"
        )
    )


    combined = " ".join(
        [
            title,
            description,
            content,
        ]
    )


    score = 0


    for keyword in (
        FUNDAMENTAL_SEARCH_KEYWORDS
    ):

        keyword = lower_text(
            keyword
        )


        if not keyword:

            continue


        if keyword in title:

            score += 5


        elif keyword in combined:

            score += 2


    # =====================================================
    # Gold langsung lebih relevan
    # =====================================================

    if (
        "gold"
        in title
    ):

        score += 8


    if (
        "xau"
        in title
    ):

        score += 8


    return score


# =========================================================
# FRESHNESS SCORE
# =========================================================

def freshness_score(
    news: Dict[str, Any],
) -> int:

    age = news_age_minutes(
        news
    )


    if age is None:

        return 0


    if age < 0:

        return 0


    if age <= 15:

        return 10


    if age <= 30:

        return 8


    if age <= 60:

        return 6


    if age <= 180:

        return 4


    if age <= 360:

        return 2


    return 1


# =========================================================
# TOTAL SCORE
# =========================================================

def news_score(
    news: Dict[str, Any],
) -> int:

    source = normalize_text(
        news.get(
            "source"
        )
    )


    return (
        relevance_score(
            news
        )
        + source_priority_score(
            source
        )
        + freshness_score(
            news
        )
    )


# =========================================================
# NORMALIZE NEWS ITEM
# =========================================================

def normalize_news_item(
    item: Dict[str, Any],
) -> Dict[str, Any]:

    """
    Mengubah berbagai bentuk response API menjadi
    struktur standar internal.
    """

    if not isinstance(
        item,
        dict,
    ):

        return {}


    # =====================================================
    # TITLE
    # =====================================================

    title = (
        item.get("title")
        or item.get("headline")
        or item.get("name")
        or ""
    )


    # =====================================================
    # DESCRIPTION
    # =====================================================

    description = (
        item.get("description")
        or item.get("summary")
        or item.get("excerpt")
        or ""
    )


    # =====================================================
    # CONTENT
    # =====================================================

    content = (
        item.get("content")
        or item.get("body")
        or item.get("text")
        or ""
    )


    # =====================================================
    # URL
    # =====================================================

    url = (
        item.get("url")
        or item.get("link")
        or item.get("article_url")
        or ""
    )


    # =====================================================
    # SOURCE
    # =====================================================

    source = ""


    source_data = (
        item.get(
            "source"
        )
    )


    if isinstance(
        source_data,
        dict,
    ):

        source = (
            source_data.get(
                "name"
            )
            or source_data.get(
                "title"
            )
            or ""
        )

    else:

        source = (
            source_data
            or item.get(
                "publisher"
            )
            or item.get(
                "site"
            )
            or ""
        )


    # =====================================================
    # PUBLISHED DATE
    # =====================================================

    published_at = (
        item.get(
            "published_at"
        )
        or item.get(
            "publishedAt"
        )
        or item.get(
            "published"
        )
        or item.get(
            "pubDate"
        )
        or item.get(
            "date"
        )
        or item.get(
            "datetime"
        )
        or ""
    )


    # =====================================================
    # IMAGE
    # =====================================================

    image = (
        item.get(
            "image"
        )
        or item.get(
            "urlToImage"
        )
        or ""
    )


    return {

        "title": normalize_text(
            title
        ),

        "description": normalize_text(
            description
        ),

        "content": normalize_text(
            content
        ),

        "url": normalize_text(
            url
        ),

        "source": normalize_text(
            source
        ),

        "published_at": normalize_text(
            published_at
        ),

        "image": normalize_text(
            image
        ),

    }


# =========================================================
# EXTRACT ARTICLES
# =========================================================

def extract_articles(
    data: Any,
) -> List[Dict[str, Any]]:

    if isinstance(
        data,
        list,
    ):

        return [
            item
            for item in data
            if isinstance(
                item,
                dict
            )
        ]


    if not isinstance(
        data,
        dict,
    ):

        return []


    # =====================================================
    # Common API keys
    # =====================================================

    possible_keys = [

        "articles",

        "data",

        "results",

        "news",

        "items",

    ]


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


    # =====================================================
    # Single article
    # =====================================================

    if any(
        key in data
        for key in (
            "title",
            "headline",
            "url",
            "link",
        )
    ):

        return [
            data
        ]


    return []


# =========================================================
# BUILD API PARAMS
# =========================================================

def build_api_params() -> Dict[str, Any]:

    """
    Parameter generic.

    Jika NEWS_API_URL Anda menggunakan provider tertentu,
    parameter dapat disesuaikan kemudian tanpa menyentuh
    SMC.
    """

    query = " OR ".join(
        FUNDAMENTAL_SEARCH_KEYWORDS[
            :10
        ]
    )


    params = {

        "apiKey": NEWS_API_KEY,

        "q": query,

        "language": NEWS_SOURCE_LANGUAGE,

        "pageSize": NEWS_FETCH_LIMIT,

        "sortBy": "publishedAt",

    }


    return params


# =========================================================
# FETCH NEWS
# =========================================================

def fetch_news() -> List[Dict[str, Any]]:

    """
    Mengambil kandidat berita dari NEWS_API_URL.
    """

    if not FUNDAMENTAL_ENABLED:

        logger.info(
            "Fundamental service disabled."
        )

        return []


    if not NEWS_API_KEY:

        logger.warning(
            "NEWS_API_KEY belum diisi."
        )

        return []


    if not NEWS_API_URL:

        logger.warning(
            "NEWS_API_URL belum diisi."
        )

        return []


    params = build_api_params()


    try:

        logger.info(
            "Mengambil berita fundamental | "
            "url=%s",
            NEWS_API_URL,
        )


        response = requests.get(

            NEWS_API_URL,

            params=params,

            timeout=NEWS_REQUEST_TIMEOUT,

        )


        response.raise_for_status()


        data = response.json()


        articles = extract_articles(
            data
        )


        logger.info(
            "News provider mengembalikan %s kandidat.",
            len(articles),
        )


        normalized = []


        for item in articles:

            news = normalize_news_item(
                item
            )


            if news.get(
                "title"
            ):

                normalized.append(
                    news
                )


        return normalized


    except requests.RequestException as e:

        logger.error(
            "Request fundamental news gagal: %s",
            repr(e),
        )

        return []


    except ValueError as e:

        logger.error(
            "Response fundamental news bukan JSON valid: %s",
            repr(e),
        )

        return []


    except Exception:

        logger.exception(
            "Error tidak terduga saat mengambil berita."
        )

        return []


# =========================================================
# VALIDATE NEWS
# =========================================================

def validate_news(
    news: Dict[str, Any],
) -> bool:

    if not news:

        return False


    # =====================================================
    # TITLE
    # =====================================================

    if not news.get(
        "title"
    ):

        return False


    # =====================================================
    # SOURCE
    # =====================================================

    if NEWS_REQUIRE_SOURCE:

        if not news.get(
            "source"
        ):

            logger.debug(
                "News ditolak: source kosong | %s",
                news.get(
                    "title"
                ),
            )

            return False


    # =====================================================
    # URL
    # =====================================================

    if NEWS_REQUIRE_URL:

        if not is_valid_url(
            news.get(
                "url"
            )
        ):

            logger.debug(
                "News ditolak: URL tidak valid | %s",
                news.get(
                    "title"
                ),
            )

            return False


    # =====================================================
    # BLOCKED
    # =====================================================

    if contains_blocked_keyword(
        news
    ):

        logger.info(
            "News ditolak karena blocked keyword | %s",
            news.get(
                "title"
            ),
        )

        return False


    # =====================================================
    # RELEVANT
    # =====================================================

    if not contains_relevant_keyword(
        news
    ):

        logger.debug(
            "News ditolak karena tidak relevan | %s",
            news.get(
                "title"
            ),
        )

        return False


    # =====================================================
    # AGE
    # =====================================================

    if is_news_too_old(
        news
    ):

        logger.debug(
            "News ditolak karena terlalu lama | %s",
            news.get(
                "title"
            ),
        )

        return False


    return True


# =========================================================
# SELECT BEST NEWS
# =========================================================

def select_best_news(
    articles: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:

    valid_articles = []


    for article in articles:

        if not validate_news(
            article
        ):

            continue


        # ================================================
        # DUPLICATE
        # ================================================

        if NEWS_PREVENT_DUPLICATE:

            if is_news_seen(
                article
            ):

                logger.debug(
                    "News duplicate dilewati | %s",
                    article.get(
                        "title"
                    ),
                )

                continue


        valid_articles.append(
            article
        )


    if not valid_articles:

        logger.warning(
            "Tidak ada fundamental news valid."
        )

        return None


    # =====================================================
    # SORT
    # =====================================================

    valid_articles.sort(

        key=news_score,

        reverse=True,

    )


    best = (
        valid_articles[0]
    )


    best["score"] = news_score(
        best
    )


    logger.info(
        "Fundamental news terpilih | "
        "score=%s | source=%s | title=%s",
        best["score"],
        best.get(
            "source"
        ),
        best.get(
            "title"
        ),
    )


    return best


# =========================================================
# GOLD IMPACT
# =========================================================

def detect_gold_impact(
    news: Dict[str, Any],
) -> str:

    """
    Estimasi arah fundamental terhadap Gold.

    Return:
        BULLISH
        BEARISH
        NEUTRAL
    """

    if not news:

        return "NEUTRAL"


    text = lower_text(
        " ".join(
            [
                news.get(
                    "title",
                    ""
                ),
                news.get(
                    "description",
                    ""
                ),
                news.get(
                    "content",
                    ""
                ),
            ]
        )
    )


    bullish_score = 0

    bearish_score = 0


    # =====================================================
    # BULLISH GOLD
    # =====================================================

    bullish_keywords = [

        "gold rises",

        "gold gains",

        "gold climbs",

        "gold higher",

        "gold rally",

        "gold surge",

        "gold demand",

        "safe haven",

        "dovish",

        "rate cut",

        "rate cuts",

        "lower rates",

        "falling yields",

        "weaker dollar",

        "weak dollar",

        "dollar falls",

        "dollar weakens",

        "geopolitical tension",

        "geopolitical tensions",

        "war",

        "uncertainty",

    ]


    # =====================================================
    # BEARISH GOLD
    # =====================================================

    bearish_keywords = [

        "gold falls",

        "gold drops",

        "gold declines",

        "gold lower",

        "gold selloff",

        "gold slump",

        "hawkish",

        "rate hike",

        "rate hikes",

        "higher rates",

        "rising yields",

        "stronger dollar",

        "strong dollar",

        "dollar rises",

        "dollar strengthens",

    ]


    for keyword in bullish_keywords:

        if keyword in text:

            bullish_score += 1


    for keyword in bearish_keywords:

        if keyword in text:

            bearish_score += 1


    # =====================================================
    # RATE / YIELD LOGIC
    # =====================================================

    if (
        "treasury yield"
        in text
        or "treasury yields"
        in text
        or "us yields"
        in text
        or "bond yields"
        in text
    ):

        if (
            "fall"
            in text
            or "decline"
            in text
            or "lower"
            in text
            or "drop"
            in text
        ):

            bullish_score += 2


        if (
            "rise"
            in text
            or "increase"
            in text
            or "higher"
            in text
            or "surge"
            in text
        ):

            bearish_score += 2


    # =====================================================
    # USD
    # =====================================================

    if (
        "us dollar"
        in text
        or "dollar"
        in text
        or "usd"
        in text
    ):

        if (
            "weaken"
            in text
            or "weak"
            in text
            or "fall"
            in text
            or "decline"
            in text
        ):

            bullish_score += 2


        if (
            "strengthen"
            in text
            or "strong"
            in text
            or "rise"
            in text
            or "gain"
            in text
        ):

            bearish_score += 2


    # =====================================================
    # FINAL
    # =====================================================

    if bullish_score > bearish_score:

        return "BULLISH"


    if bearish_score > bullish_score:

        return "BEARISH"


    return "NEUTRAL"


# =========================================================
# TRANSLATION
# =========================================================

def translate_to_indonesian(
    text: str,
) -> str:

    """
    Placeholder translation layer.

    Sengaja tidak menggunakan API AI di file ini.

    Tujuannya supaya fundamental service tetap stabil.

    Jika nanti kita menggunakan OpenAI / Gemini / AI lain,
    fungsi ini dapat diganti tanpa mengubah SMC.
    """

    text = normalize_text(
        text
    )


    if not text:

        return ""


    # =====================================================
    # Jika output memang bukan Indonesia,
    # translation provider dapat ditambahkan kemudian.
    # =====================================================

    return text


# =========================================================
# BUILD SUMMARY
# =========================================================

def build_summary(
    news: Dict[str, Any],
) -> str:

    description = normalize_text(
        news.get(
            "description"
        )
    )


    content = normalize_text(
        news.get(
            "content"
        )
    )


    summary = (
        description
        or content
    )


    if not summary:

        summary = (
            news.get(
                "title"
            )
            or ""
        )


    # =====================================================
    # BATAS SUMMARY
    # =====================================================

    if len(
        summary
    ) > 500:

        summary = (
            summary[:497]
            + "..."
        )


    if (
        NEWS_TRANSLATE_TO_INDONESIAN
        and FUNDAMENTAL_LANGUAGE == "id"
    ):

        summary = translate_to_indonesian(
            summary
        )


    return summary


# =========================================================
# ENRICH NEWS
# =========================================================

def enrich_news(
    news: Dict[str, Any],
) -> Dict[str, Any]:

    result = dict(
        news
    )


    # =====================================================
    # GOLD IMPACT
    # =====================================================

    if NEWS_ENABLE_GOLD_IMPACT:

        result[
            "gold_impact"
        ] = detect_gold_impact(
            result
        )

    else:

        result[
            "gold_impact"
        ] = "NEUTRAL"


    # =====================================================
    # SUMMARY
    # =====================================================

    if NEWS_ENABLE_SUMMARY:

        result[
            "summary"
        ] = build_summary(
            result
        )

    else:

        result[
            "summary"
        ] = ""


    # =====================================================
    # AGE
    # =====================================================

    result[
        "age_minutes"
    ] = news_age_minutes(
        result
    )


    # =====================================================
    # SCORE
    # =====================================================

    result[
        "score"
    ] = news_score(
        result
    )


    return result


# =========================================================
# GET LATEST FUNDAMENTAL NEWS
# =========================================================

def get_latest_fundamental_news(
) -> Optional[Dict[str, Any]]:

    """
    Fungsi utama.

    Return:
        1 berita fundamental valid
        atau None
    """

    if not FUNDAMENTAL_ENABLED:

        logger.info(
            "Fundamental disabled."
        )

        return None


    articles = fetch_news()


    if not articles:

        logger.warning(
            "Tidak ada kandidat berita."
        )

        return None


    best = select_best_news(
        articles
    )


    if best is None:

        return None


    best = enrich_news(
        best
    )


    # =====================================================
    # MARK SEEN
    # =====================================================

    if NEWS_PREVENT_DUPLICATE:

        mark_news_seen(
            best
        )


    return best


# =========================================================
# GET MULTIPLE NEWS
# =========================================================

def get_fundamental_news(
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:

    """
    Mengambil beberapa berita valid.

    Default tetap mengikuti:
        FUNDAMENTAL_NEWS_PER_UPDATE
    """

    if not FUNDAMENTAL_ENABLED:

        return []


    if limit is None:

        limit = (
            FUNDAMENTAL_NEWS_PER_UPDATE
        )


    try:

        limit = int(
            limit
        )

    except (
        ValueError,
        TypeError,
    ):

        limit = 1


    if limit < 1:

        limit = 1


    articles = fetch_news()


    if not articles:

        return []


    valid = []


    for article in articles:

        if not validate_news(
            article
        ):

            continue


        if NEWS_PREVENT_DUPLICATE:

            if is_news_seen(
                article
            ):

                continue


        valid.append(
            article
        )


    valid.sort(

        key=news_score,

        reverse=True,

    )


    selected = valid[
        :limit
    ]


    result = []


    for article in selected:

        enriched = enrich_news(
            article
        )


        result.append(
            enriched
        )


        if NEWS_PREVENT_DUPLICATE:

            mark_news_seen(
                enriched
            )


    return result


# =========================================================
# FORMAT TELEGRAM
# =========================================================

def format_fundamental_news(
    news: Dict[str, Any],
) -> str:

    """
    Format berita fundamental untuk Telegram.

    Tidak bergantung pada format SMC.
    """

    if not news:

        return (
            "📰 *FUNDAMENTAL GOLD*\n"
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


    url = normalize_text(
        news.get(
            "url"
        )
    )


    summary = normalize_text(
        news.get(
            "summary"
        )
    )


    impact = normalize_text(
        news.get(
            "gold_impact",
            "NEUTRAL"
        )
    )


    published = normalize_text(
        news.get(
            "published_at"
        )
    )


    # =====================================================
    # IMPACT ICON
    # =====================================================

    if impact == "BULLISH":

        impact_text = (
            "🟢 BULLISH GOLD"
        )


    elif impact == "BEARISH":

        impact_text = (
            "🔴 BEARISH GOLD"
        )


    else:

        impact_text = (
            "🟡 NEUTRAL / MIXED"
        )


    # =====================================================
    # MESSAGE
    # =====================================================

    lines = [

        "📰 *FUNDAMENTAL GOLD*",

        "━━━━━━━━━━━━━━━━━━",

        "",

        f"🗞 *{title}*",

        "",

        f"📊 Impact: *{impact_text}*",

        f"🏦 Source: *{source or 'Unknown'}*",

    ]


    if published:

        lines.append(
            f"🕐 Published: {published}"
        )


    if summary:

        lines.extend(
            [
                "",
                "📝 *Ringkasan*",
                summary,
            ]
        )


    if url:

        lines.extend(
            [
                "",
                f"🔗 [Sumber Asli]({url})",
            ]
        )


    return "\n".join(
        lines
    )


# =========================================================
# COMBINED DATA
# =========================================================

def build_combined_fundamental_context(
    news: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    """
    Menyiapkan data fundamental yang nanti diberikan
    ke Combined AI.

    Tidak melakukan perubahan terhadap TradeSignal SMC.
    """

    if not news:

        return {

            "available": False,

            "title": "",

            "source": "",

            "url": "",

            "summary": "",

            "gold_impact": "NEUTRAL",

            "published_at": "",

            "age_minutes": None,

        }


    return {

        "available": True,

        "title": normalize_text(
            news.get(
                "title"
            )
        ),

        "source": normalize_text(
            news.get(
                "source"
            )
        ),

        "url": normalize_text(
            news.get(
                "url"
            )
        ),

        "summary": normalize_text(
            news.get(
                "summary"
            )
        ),

        "gold_impact": normalize_text(
            news.get(
                "gold_impact",
                "NEUTRAL"
            )
        ),

        "published_at": normalize_text(
            news.get(
                "published_at"
            )
        ),

        "age_minutes": news.get(
            "age_minutes"
        ),

    }


# =========================================================
# HEALTH CHECK
# =========================================================

def fundamental_health_check() -> Dict[str, Any]:

    return {

        "enabled": FUNDAMENTAL_ENABLED,

        "api_key_configured": bool(
            NEWS_API_KEY
        ),

        "api_url_configured": bool(
            NEWS_API_URL
        ),

        "news_per_update": (
            FUNDAMENTAL_NEWS_PER_UPDATE
        ),

        "max_age_hours": (
            FUNDAMENTAL_MAX_NEWS_AGE_HOURS
        ),

        "cache_file": (
            FUNDAMENTAL_NEWS_CACHE_FILE
        ),

    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )


    logger.info(
        "Fundamental Service Test"
    )


    logger.info(
        "Health: %s",
        fundamental_health_check()
    )


    news = get_latest_fundamental_news()


    if news:

        print(
            format_fundamental_news(
                news
            )
        )

    else:

        print(
            "Tidak ada berita fundamental valid."
        )
