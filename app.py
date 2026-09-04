from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from flask import Flask, render_template, request
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

app = Flask(__name__)

DEFAULT_CITY = "大阪市"
DEFAULT_LAT = 34.6937
DEFAULT_LON = 135.5023
CACHE_FILE = Path("/tmp/uniform_weather_cache.json")

WEATHER_META = {
    0: ("晴れ", "sun"),
    1: ("晴れ", "sun"),
    2: ("晴れ時々くもり", "cloud-sun"),
    3: ("くもり", "cloud"),
    45: ("霧", "cloud-fog"),
    48: ("霧", "cloud-fog"),
    51: ("小雨", "cloud-drizzle"),
    53: ("小雨", "cloud-drizzle"),
    55: ("雨", "cloud-rain"),
    61: ("小雨", "cloud-rain"),
    63: ("雨", "cloud-rain"),
    65: ("強い雨", "cloud-rain-wind"),
    71: ("雪", "cloud-snow"),
    73: ("雪", "cloud-snow"),
    75: ("大雪", "snowflake"),
    80: ("にわか雨", "cloud-sun-rain"),
    81: ("にわか雨", "cloud-rain"),
    82: ("強いにわか雨", "cloud-rain-wind"),
    95: ("雷雨", "cloud-lightning"),
    96: ("雷雨", "cloud-lightning"),
    99: ("雷雨", "cloud-lightning"),
}

SYMBOL_META = {
    "clearsky": ("晴れ", "sun"),
    "fair": ("晴れ", "sun"),
    "partlycloudy": ("晴れ時々くもり", "cloud-sun"),
    "cloudy": ("くもり", "cloud"),
    "fog": ("霧", "cloud-fog"),
    "lightrain": ("小雨", "cloud-drizzle"),
    "rain": ("雨", "cloud-rain"),
    "heavyrain": ("強い雨", "cloud-rain-wind"),
    "lightrainshowers": ("にわか雨", "cloud-sun-rain"),
    "rainshowers": ("にわか雨", "cloud-rain"),
    "heavyrainshowers": ("強いにわか雨", "cloud-rain-wind"),
    "lightsnow": ("雪", "cloud-snow"),
    "snow": ("雪", "cloud-snow"),
    "heavysnow": ("大雪", "snowflake"),
    "sleet": ("みぞれ", "cloud-snow"),
    "rainandthunder": ("雷雨", "cloud-lightning"),
    "heavyrainandthunder": ("雷雨", "cloud-lightning"),
}

OUTFIT_LIBRARY = {
    "girls": [
        {
            "id": "girl-summer",
            "image": "girl_summer.jpg",
            "title": "半袖シャツ × 夏スカート",
            "description": "暑い日は、涼しく動きやすい夏制服がおすすめ。",
            "tags": ["半袖シャツ", "夏スカート", "リボン", "ローファー"],
            "kind": "summer",
        },
        {
            "id": "girl-vest",
            "image": "girl_vest.jpg",
            "title": "長袖シャツ × ニットベスト",
            "description": "朝晩の気温差に対応しやすい、過ごしやすい定番コーデ。",
            "tags": ["長袖シャツ", "ニットベスト", "スカート", "リボン"],
            "kind": "vest",
        },
        {
            "id": "girl-cardigan",
            "image": "girl_cardigan.jpg",
            "title": "長袖シャツ × カーディガン",
            "description": "肌寒い日は、上着を重ねて体温調整しやすく。",
            "tags": ["長袖シャツ", "カーディガン", "スカート", "ローファー"],
            "kind": "blazer",
        },
    ],
    "boys": [
        {
            "id": "boy-summer",
            "image": "boy_summer.jpg",
            "title": "半袖シャツ × 夏スラックス",
            "description": "暑い日は、通気性のいい夏制服で涼しく快適に。",
            "tags": ["半袖シャツ", "夏スラックス", "ベルト", "ローファー"],
            "kind": "summer",
        },
        {
            "id": "boy-vest",
            "image": "boy_vest.jpg",
            "title": "長袖シャツ × ニットベスト",
            "description": "朝晩の気温差に合わせやすい、スマートな定番コーデ。",
            "tags": ["長袖シャツ", "ニットベスト", "ネクタイ", "スラックス"],
            "kind": "vest",
        },
        {
            "id": "boy-blazer",
            "image": "boy_blazer.jpg",
            "title": "長袖シャツ × ブレザー",
            "description": "気温が低い日は、ブレザーでしっかり防寒。",
            "tags": ["長袖シャツ", "ブレザー", "ネクタイ", "スラックス"],
            "kind": "blazer",
        },
    ],
}


def http_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.45,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "UniformWeatherApp/1.0 (+https://github.com/yuyajames133/uniform-weather-app)"
    })
    return session


SESSION = http_session()


def geocode_city(city_name: str) -> dict[str, Any] | None:
    # Primary: Open-Meteo geocoding
    try:
        r = SESSION.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city_name, "count": 1, "language": "ja",
                "format": "json", "countryCode": "JP",
            },
            timeout=(4, 8),
        )
        r.raise_for_status()
        rows = r.json().get("results") or []
        if rows:
            row = rows[0]
            return {
                "name": f"{row.get('admin1') or ''} {row.get('name') or city_name}".strip(),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }
    except Exception:
        pass

    # Secondary: OpenStreetMap Nominatim
    try:
        r = SESSION.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{city_name}, Japan", "format": "jsonv2", "limit": 1, "accept-language": "ja"},
            timeout=(4, 8),
        )
        r.raise_for_status()
        rows = r.json()
        if rows:
            return {
                "name": city_name,
                "latitude": float(rows[0]["lat"]),
                "longitude": float(rows[0]["lon"]),
            }
    except Exception:
        pass
    return None


def fetch_open_meteo(lat: float, lon: float) -> dict[str, Any]:
    r = SESSION.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": ",".join([
                "temperature_2m", "apparent_temperature", "relative_humidity_2m",
                "weather_code", "precipitation", "wind_speed_10m",
            ]),
            "hourly": "temperature_2m,precipitation_probability",
            "daily": ",".join([
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "precipitation_probability_max",
            ]),
            "timezone": "Asia/Tokyo",
            "forecast_days": 7,
        },
        timeout=(4, 10),
    )
    r.raise_for_status()
    data = r.json()
    if "current" not in data or "daily" not in data:
        raise ValueError("Open-Meteo response missing fields")
    data["_provider"] = "Open-Meteo"
    return data


def symbol_to_meta(symbol: str) -> tuple[str, str]:
    base = symbol.replace("_day", "").replace("_night", "").replace("_polartwilight", "")
    for key, value in SYMBOL_META.items():
        if base.startswith(key):
            return value
    return ("天気", "cloud-sun")


def fetch_met_norway(lat: float, lon: float) -> dict[str, Any]:
    r = SESSION.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact",
        params={"lat": round(lat, 4), "lon": round(lon, 4)},
        timeout=(4, 10),
    )
    r.raise_for_status()
    series = r.json()["properties"]["timeseries"]
    if not series:
        raise ValueError("MET Norway response empty")

    now = series[0]
    inst = now["data"]["instant"]["details"]
    next1 = now["data"].get("next_1_hours", {})
    symbol = next1.get("summary", {}).get("symbol_code", "cloudy")
    label, icon = symbol_to_meta(symbol)
    precip_now = float(next1.get("details", {}).get("precipitation_amount", 0) or 0)

    days = defaultdict(lambda: {"temps": [], "rain": [], "symbol": None})
    hourly_times, hourly_temps, hourly_rain = [], [], []

    for point in series:
        t = point["time"]
        details = point["data"]["instant"]["details"]
        date = t[:10]
        temp = float(details.get("air_temperature", 0))
        days[date]["temps"].append(temp)

        n1 = point["data"].get("next_1_hours", {})
        pop = n1.get("details", {}).get("probability_of_precipitation")
        amount = n1.get("details", {}).get("precipitation_amount", 0) or 0
        if pop is None:
            pop = 80 if float(amount) >= 0.5 else 40 if float(amount) > 0 else 10
        days[date]["rain"].append(int(round(float(pop))))
        if days[date]["symbol"] is None:
            days[date]["symbol"] = n1.get("summary", {}).get("symbol_code", "cloudy")

        if len(hourly_times) < 24:
            hourly_times.append(t[:16])
            hourly_temps.append(temp)
            hourly_rain.append(int(round(float(pop))))

    sorted_days = sorted(days)[:7]
    daily_codes = []
    daily_max, daily_min, daily_rain = [], [], []
    for date in sorted_days:
        meta = symbol_to_meta(days[date]["symbol"] or "cloudy")
        # Encode synthetic codes only for our template; label/icon are overridden below.
        daily_codes.append(2 if "晴れ" in meta[0] else 61 if "雨" in meta[0] else 3)
        daily_max.append(max(days[date]["temps"]))
        daily_min.append(min(days[date]["temps"]))
        daily_rain.append(max(days[date]["rain"] or [0]))

    current_pop = daily_rain[0] if daily_rain else 0

    return {
        "current": {
            "time": now["time"][:16],
            "temperature_2m": float(inst.get("air_temperature", 0)),
            "apparent_temperature": float(inst.get("air_temperature", 0)),
            "relative_humidity_2m": float(inst.get("relative_humidity", 0)),
            "weather_code": 2 if "晴れ" in label else 61 if "雨" in label else 3,
            "precipitation": precip_now,
            "wind_speed_10m": float(inst.get("wind_speed", 0)) * 3.6,
            "_label": label,
            "_icon": icon,
        },
        "hourly": {
            "time": hourly_times,
            "temperature_2m": hourly_temps,
            "precipitation_probability": hourly_rain,
        },
        "daily": {
            "time": sorted_days,
            "weather_code": daily_codes,
            "temperature_2m_max": daily_max,
            "temperature_2m_min": daily_min,
            "precipitation_probability_max": daily_rain,
        },
        "_provider": "MET Norway",
    }


def cache_key(lat: float, lon: float) -> str:
    return f"{round(lat,2)},{round(lon,2)}"


def load_cache(lat: float, lon: float) -> dict[str, Any] | None:
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return payload.get(cache_key(lat, lon))
    except Exception:
        return None


def save_cache(lat: float, lon: float, data: dict[str, Any]) -> None:
    try:
        payload = {}
        if CACHE_FILE.exists():
            payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        payload[cache_key(lat, lon)] = data
        CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def fetch_weather(lat: float, lon: float) -> tuple[dict[str, Any], str]:
    errors = []
    for provider in (fetch_open_meteo, fetch_met_norway):
        try:
            data = provider(lat, lon)
            save_cache(lat, lon, data)
            return data, data.get("_provider", "Weather API")
        except Exception as exc:
            errors.append(f"{provider.__name__}: {exc}")

    cached = load_cache(lat, lon)
    if cached:
        return cached, f"{cached.get('_provider', 'Weather API')}・前回取得"

    raise RuntimeError(" / ".join(errors))


def outfit_kind(temp: float, rain_probability: int, wind_speed: float) -> str:
    effective = temp
    if rain_probability >= 60:
        effective -= 1.5
    if wind_speed >= 18:
        effective -= 1.5
    if effective >= 26:
        return "summer"
    if effective >= 20:
        return "vest"
    return "blazer"


def day_advice(temp: float, rain_probability: int, wind_speed: float) -> list[str]:
    rows = []
    if rain_probability >= 60:
        rows.append("折りたたみ傘を忘れずに。濡れた時用のタオルもあると安心。")
    elif rain_probability >= 30:
        rows.append("にわか雨に備えて、折りたたみ傘があると安心。")
    if temp >= 28:
        rows.append("汗をかきやすいので、吸汗速乾インナーと水分補給を意識。")
    elif temp <= 18:
        rows.append("朝晩は冷えやすいので、ブレザーやカーディガンで調整。")
    else:
        rows.append("朝晩と昼の気温差に合わせて、脱ぎ着できるアイテムを。")
    if wind_speed >= 18:
        rows.append("風が強め。上着があると安心です。")
    return rows


def selected_outfits(kind: str) -> dict[str, dict[str, Any]]:
    result = {}
    for gender, rows in OUTFIT_LIBRARY.items():
        match = next((row for row in rows if row["kind"] == kind), rows[0])
        result[gender] = dict(match)
    return result


@app.route("/")
def index():
    city_query = request.args.get("city", "").strip()
    city_name = DEFAULT_CITY
    lat, lon = DEFAULT_LAT, DEFAULT_LON
    location_notice = None

    if city_query:
        place = geocode_city(city_query)
        if place:
            city_name = place["name"]
            lat, lon = place["latitude"], place["longitude"]
        else:
            location_notice = f"「{city_query}」が見つからなかったため大阪市を表示しています。"

    try:
        raw, provider = fetch_weather(lat, lon)
        weather_error = None
    except Exception:
        # Do not fake live weather. Render a clear retry state.
        raw, provider, weather_error = None, None, "天気データを取得できませんでした。再読み込みしてください。"

    if raw is None:
        return render_template(
            "error.html",
            city_name=city_name,
            message=weather_error,
        ), 503

    current = raw["current"]
    daily = raw["daily"]
    hourly = raw["hourly"]

    temp = round(float(current["temperature_2m"]), 1)
    apparent = round(float(current.get("apparent_temperature", temp)), 1)
    humidity = int(round(float(current.get("relative_humidity_2m", 0))))
    wind = round(float(current.get("wind_speed_10m", 0)), 1)
    code = int(current.get("weather_code", 2))
    weather_label, weather_icon = WEATHER_META.get(code, ("天気", "cloud-sun"))
    weather_label = current.get("_label", weather_label)
    weather_icon = current.get("_icon", weather_icon)

    rain_prob = int(daily["precipitation_probability_max"][0] or 0)
    max_temp = round(float(daily["temperature_2m_max"][0]), 1)
    min_temp = round(float(daily["temperature_2m_min"][0]), 1)

    kind = outfit_kind(temp, rain_prob, wind)
    outfits = selected_outfits(kind)

    week = []
    for i, date in enumerate(daily["time"][:7]):
        dcode = int(daily["weather_code"][i])
        dlabel, dicon = WEATHER_META.get(dcode, ("天気", "cloud-sun"))
        day_rain = int(daily["precipitation_probability_max"][i] or 0)
        day_max = float(daily["temperature_2m_max"][i])
        week.append({
            "date": date, "label": dlabel, "icon": dicon,
            "max": round(day_max), "min": round(float(daily["temperature_2m_min"][i])),
            "rain": day_rain, "kind": outfit_kind(day_max, day_rain, wind),
        })

    weather = {
        "temp": temp, "apparent": apparent, "humidity": humidity, "wind": wind,
        "label": weather_label, "icon": weather_icon, "rain_probability": rain_prob,
        "max": max_temp, "min": min_temp,
        "updated": current.get("time", "").replace("T", " "),
        "provider": provider,
    }

    return render_template(
        "index.html",
        city_name=city_name,
        city_query=city_query,
        weather=weather,
        outfits=outfits,
        week=week,
        advice=day_advice(temp, rain_prob, wind),
        recommended_kind=kind,
        notice=location_notice,
    )


if __name__ == "__main__":
    app.run(debug=True)
