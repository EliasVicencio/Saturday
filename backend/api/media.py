# api/media.py - Weather/News/Crypto/YouTube Blueprint
from flask import Blueprint, request, jsonify
import logging
import os

logger = logging.getLogger("saturday.media")

media_bp = Blueprint("media", __name__)

_saturday = None

def init_media(saturday):
    global _saturday
    _saturday = saturday

@media_bp.route("/api/weather", methods=["GET"])
def weather():
    from api.auth import require_api_key
    from modules.http_utils import get_with_retry
    city = request.args.get("city", os.getenv("SATURDAY_CITY", "Santiago"))
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return jsonify({"error": "WEATHER_API_KEY no configurada"}), 500
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
        response = get_with_retry(url, timeout=10)
        if not response or response.status_code != 200:
            return jsonify({"error": "Error obteniendo el clima"}), 502
        data = response.json()
        return jsonify({
            "temp": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "condition": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"],
            "city": data.get("name", city),
            "country": data.get("sys", {}).get("country", ""),
        })
    except Exception as e:
        logger.error("Error en /api/weather: %s", e)
        return jsonify({"error": "Error obteniendo clima"}), 500

@media_bp.route("/api/news", methods=["GET"])
def news():
    from api.auth import require_api_key
    result = _saturday.get_news()
    return jsonify({"news": result})

@media_bp.route("/api/news/headlines", methods=["GET"])
def news_headlines():
    from api.auth import require_api_key
    if not _saturday or not _saturday.news or not _saturday.news.is_available():
        return jsonify({"articles": [], "available": False})
    try:
        category = request.args.get("category")
        limit = int(request.args.get("limit", 8))
        articles = _saturday.news.get_top_headlines(category=category, limit=limit)
        return jsonify({"articles": articles, "available": True})
    except Exception as e:
        logger.error("Error en /api/news/headlines: %s", e)
        return jsonify({"articles": [], "available": True, "error": str(e)})

@media_bp.route("/api/crypto/bitcoin", methods=["GET"])
def crypto_bitcoin():
    from api.auth import require_api_key
    from modules.http_utils import get_with_retry
    try:
        response = get_with_retry(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd,clp", "include_24hr_change": "true", "include_last_updated_at": "true"},
            timeout=10,
        )
        if not response or response.status_code >= 400:
            return jsonify({"error": "Error obteniendo precio Bitcoin"}), 502
        data = response.json().get("bitcoin", {})
        if not data:
            return jsonify({"error": "Sin datos de CoinGecko"}), 502
        return jsonify({
            "usd": data.get("usd"),
            "clp": data.get("clp"),
            "usd_24h_change": round(data.get("usd_24h_change", 0), 2),
            "last_updated_at": data.get("last_updated_at"),
        })
    except Exception as e:
        logger.error("Error en /api/crypto: %s", e)
        return jsonify({"error": "Error obteniendo precio Bitcoin"}), 500

@media_bp.route("/api/youtube/search", methods=["GET"])
def youtube_search():
    from api.auth import require_api_key
    from modules.http_utils import get_with_retry
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return jsonify({"error": "YOUTUBE_API_KEY no configurada"}), 500
    query = request.args.get("q", "").strip()
    max_results = int(request.args.get("max_results", 5))
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {"part": "snippet", "q": query, "type": "video", "maxResults": max_results, "key": api_key, "relevanceLanguage": "es", "order": "relevance"}
        resp = get_with_retry(url, params=params, timeout=10)
        if not resp or resp.status_code >= 400:
            return jsonify({"error": "Error de YouTube API"}), 502
        data = resp.json()
        videos = []
        for item in data.get("items", []):
            snippet = item["snippet"]
            videos.append({
                "id": item["id"]["videoId"],
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "thumbnail": snippet["thumbnails"]["medium"]["url"],
                "published": snippet["publishedAt"],
            })
        return jsonify({"videos": videos, "query": query})
    except Exception as e:
        logger.error("Error en /api/youtube: %s", e)
        return jsonify({"error": "Error buscando videos"}), 500
