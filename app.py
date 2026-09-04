from __future__ import annotations

import json
from collections import defaultdict
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

WMO = {
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

OUTFITS = {
    "boys": {
        "summer": {
            "image": "boy_summer.jpg",
            "title": "半袖シャツ × 夏スラックス",
            "description": "暑い日は、通気性のいい夏制服で涼しく快適に。",
            "items": ["半袖シャツ", "夏スラックス", "ネクタイ", "ローファー"],
        },
        "vest": {
            "image": "boy_vest.jpg",
            "title": "長袖シャツ × ニットベスト",
            "description": "朝晩の気温差に合わせやすい、すっきりした定番コーデ。",
            "items": ["長袖シャツ", "ニットベスト", "ネクタイ", "スラックス"],
        },
        "blazer": {
            "image": "boy_blazer.jpg",
            "title": "長袖シャツ × ブレザー",
            "description": "肌寒い日は、ブレザーを重ねてきちんと暖かく。",
            "items": ["長袖シャツ", "ブレザー", "ネクタイ", "スラックス"],
        },
    },
    "girls": {
        "summer": {
            "image": "girl_summer.jpg",
            "title": "半袖シャツ × 夏スカート",
            "description": "暑い日は、軽やかな夏制服で爽やかに。",
            "items": ["半袖シャツ", "夏スカート", "リボン", "ローファー"],
        },
        "vest": {
            "image": "girl_vest.jpg",
            "title": "長袖シャツ × ニットベスト",
            "description": "朝晩の気温差に合わせやすい、上品で動きやすいコーデ。",
            "items": ["長袖シャツ", "ニットベスト", "リボン", "スカート"],
        },
        "blazer": {
            "image": "girl_cardigan.jpg",
            "title": "長袖シャツ × カーディガン",
            "description": "肌寒い日は、カーディガンでやわらかく体温調整。",
            "items": ["長袖シャツ", "カーディガン", "リボン", "スカート"],
        },
    },
}


def build_session() -> requests.Session:
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "UniformWeather/1.0",
    })
    return session


HTTP = build_session()


def geocode_city(city: str) -> dict[str, Any] | None:
    try:
        r = HTTP.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1,
                "language": "ja",
                "format": "json",
                "countryCode": "JP",
            },
            timeout=(4, 8),
        )
        r.raise_for_status()
        rows = r.json().get("results") or []
        if rows:
            row = rows[0]
            return {
                "name": row.get("name") or city,
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
            }
    except Exception:
        pass

    try:
        r = HTTP.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{city}, Japan",
                "format": "jsonv2",
                "limit": 1,
                "accept-language": "ja",
            },
            timeout=(4, 8),
        )
        r.raise_for_status()
        rows = r.json()
        if rows:
            return {
                "name": city,
                "lat": float(rows[0]["lat"]),
                "lon": float(rows[0]["lon"]),
            }
    except Exception:
        pass

    return None


def fetch_open_meteo(lat: float, lon: float) -> dict[str, Any]:
    r = HTTP.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": ",".join([
                "temperature_2m",
                "apparent_temperature",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
            ]),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_probability_max",
                "weather_code",
            ]),
            "timezone": "Asia/Tokyo",
            "forecast_days": 7,
        },
        timeout=(4, 10),
    )
    r.raise_for_status()
    data = r.json()
    if not data.get("current") or not data.get("daily"):
        raise ValueError("Open-Meteo response incomplete")
    data["_provider"] = "Open-Meteo"
    return data


def met_symbol(symbol: str) -> tuple[str, str]:
    symbol = symbol.lower()
    if "thunder" in symbol:
        return "雷雨", "cloud-lightning"
    if "snow" in symbol or "sleet" in symbol:
        return "雪", "cloud-snow"
    if "rain" in symbol:
        return "雨", "cloud-rain"
    if "cloudy" in symbol:
        return "くもり", "cloud"
    if "partlycloudy" in symbol:
        return "晴れ時々くもり", "cloud-sun"
    return "晴れ", "sun"


def fetch_met_norway(lat: float, lon: float) -> dict[str, Any]:
    r = HTTP.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact",
        params={"lat": round(lat, 4), "lon": round(lon, 4)},
        timeout=(4, 10),
    )
    r.raise_for_status()
    series = r.json()["properties"]["timeseries"]
    if not series:
        raise ValueError("MET Norway response empty")

    first = series[0]
    details = first["data"]["instant"]["details"]
    next1 = first["data"].get("next_1_hours", {})
    symbol = next1.get("summary", {}).get("symbol_code", "clearsky")
    label, icon = met_symbol(symbol)

    days = defaultdict(lambda: {"temps": [], "pops": [], "symbol": None})
    for row in series:
        date = row["time"][:10]
        d = row["data"]["instant"]["details"]
        days[date]["temps"].append(float(d.get("air_temperature", 0)))

        n1 = row["data"].get("next_1_hours", {})
        p = n1.get("details", {}).get("probability_of_precipitation")
        amount = float(n1.get("details", {}).get("precipitation_amount", 0) or 0)
        if p is None:
            p = 80 if amount >= 0.5 else 35 if amount > 0 else 10
        days[date]["pops"].append(int(round(float(p))))
        days[date]["symbol"] = days[date]["symbol"] or n1.get("summary", {}).get("symbol_code")

    dates = sorted(days.keys())[:7]
    maxs, mins, pops, codes = [], [], [], []
    for date in dates:
        row = days[date]
        maxs.append(max(row["temps"]))
        mins.append(min(row["temps"]))
        pops.append(max(row["pops"] or [0]))
        dlabel, _ = met_symbol(row["symbol"] or "clearsky")
        codes.append(61 if "雨" in dlabel else 3 if "くもり" in dlabel else 0)

    return {
        "current": {
            "temperature_2m": float(details.get("air_temperature", 0)),
            "apparent_temperature": float(details.get("air_temperature", 0)),
            "relative_humidity_2m": float(details.get("relative_humidity", 0)),
            "wind_speed_10m": float(details.get("wind_speed", 0)) * 3.6,
            "weather_code": 61 if "雨" in label else 3 if "くもり" in label else 0,
            "_label": label,
            "_icon": icon,
        },
        "daily": {
            "time": dates,
            "temperature_2m_max": maxs,
            "temperature_2m_min": mins,
            "precipitation_probability_max": pops,
            "weather_code": codes,
        },
        "_provider": "MET Norway",
    }


def cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 2)},{round(lon, 2)}"


def save_cache(lat: float, lon: float, data: dict[str, Any]) -> None:
    try:
        payload = {}
        if CACHE_FILE.exists():
            payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        payload[cache_key(lat, lon)] = data
        CACHE_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def load_cache(lat: float, lon: float) -> dict[str, Any] | None:
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return payload.get(cache_key(lat, lon))
    except Exception:
        return None


def get_weather(lat: float, lon: float) -> tuple[dict[str, Any], str]:
    errors = []
    for provider in (fetch_open_meteo, fetch_met_norway):
        try:
            data = provider(lat, lon)
            save_cache(lat, lon, data)
            return data, data["_provider"]
        except Exception as exc:
            errors.append(str(exc))

    cached = load_cache(lat, lon)
    if cached:
        return cached, f'{cached.get("_provider", "Weather API")}（前回取得）'

    raise RuntimeError(" / ".join(errors))


def choose_kind(temp: float, rain: int, wind: float) -> str:
    # Weather should influence the outfit, but temperature remains primary.
    effective = temp
    if rain >= 60:
        effective -= 1.0
    if wind >= 18:
        effective -= 1.0

    if effective >= 26:
        return "summer"
    if effective >= 20:
        return "vest"
    return "blazer"


def daily_point(temp: float, rain: int, wind: float) -> str:
    if temp >= 28:
        return "汗をかきやすい日。吸汗速乾インナーと水分補給があると快適。"
    if rain >= 60:
        return "雨の日は足元が冷えやすいので、濡れにくい靴と折りたたみ傘を。"
    if wind >= 18:
        return "風が強め。脱ぎ着しやすい上着があると安心。"
    if temp <= 18:
        return "朝晩は冷えやすいので、上着で無理なく体温調整しよう。"
    return "朝晩と昼の気温差に合わせて、脱ぎ着しやすい組み合わせがおすすめ。"


@app.route("/")
def index():
    city_query = request.args.get("city", "").strip()

    city_name = DEFAULT_CITY
    lat, lon = DEFAULT_LAT, DEFAULT_LON
    notice = None

    if city_query:
        place = geocode_city(city_query)
        if place:
            city_name = place["name"]
            lat, lon = place["lat"], place["lon"]
        else:
            notice = f"「{city_query}」が見つからなかったため大阪市を表示しています。"

    try:
        raw, provider = get_weather(lat, lon)
    except Exception:
        return render_template(
            "error.html",
            message="天気データを取得できませんでした。しばらくしてから再読み込みしてください。",
        ), 503

    current = raw["current"]
    daily = raw["daily"]

    temp = round(float(current["temperature_2m"]), 1)
    apparent = round(float(current.get("apparent_temperature", temp)), 1)
    humidity = int(round(float(current.get("relative_humidity_2m", 0))))
    wind = round(float(current.get("wind_speed_10m", 0)), 1)
    rain = int(daily["precipitation_probability_max"][0] or 0)
    high = round(float(daily["temperature_2m_max"][0]), 1)
    low = round(float(daily["temperature_2m_min"][0]), 1)

    code = int(current.get("weather_code", 0))
    label, icon = WMO.get(code, ("天気", "cloud-sun"))
    label = current.get("_label", label)
    icon = current.get("_icon", icon)

    kind = choose_kind(temp, rain, wind)

    weather = {
        "temp": temp,
        "apparent": apparent,
        "humidity": humidity,
        "wind": wind,
        "rain": rain,
        "high": high,
        "low": low,
        "label": label,
        "icon": icon,
        "provider": provider,
    }

    outfits = {
        "boys": OUTFITS["boys"][kind],
        "girls": OUTFITS["girls"][kind],
    }

    return render_template(
        "index.html",
        city_name=city_name,
        city_query=city_query,
        notice=notice,
        weather=weather,
        outfits=outfits,
        recommended_kind=kind,
        point=daily_point(temp, rain, wind),
    )


if __name__ == "__main__":
    app.run(debug=True)
