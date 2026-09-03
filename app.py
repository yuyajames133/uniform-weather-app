from __future__ import annotations

from datetime import datetime
from typing import Any

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

DEFAULT_CITY = "大阪市"
DEFAULT_LAT = 34.6937
DEFAULT_LON = 135.5023

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
    56: ("凍雨", "cloud-rain"),
    57: ("凍雨", "cloud-rain"),
    61: ("小雨", "cloud-rain"),
    63: ("雨", "cloud-rain"),
    65: ("強い雨", "cloud-rain-wind"),
    66: ("凍雨", "cloud-rain"),
    67: ("強い凍雨", "cloud-rain-wind"),
    71: ("雪", "cloud-snow"),
    73: ("雪", "cloud-snow"),
    75: ("大雪", "snowflake"),
    77: ("雪", "snowflake"),
    80: ("にわか雨", "cloud-sun-rain"),
    81: ("にわか雨", "cloud-rain"),
    82: ("強いにわか雨", "cloud-rain-wind"),
    85: ("にわか雪", "cloud-snow"),
    86: ("強いにわか雪", "cloud-snow"),
    95: ("雷雨", "cloud-lightning"),
    96: ("雷雨", "cloud-lightning"),
    99: ("雷雨", "cloud-lightning"),
}

OUTFIT_LIBRARY = {
    "girls": [
        {
            "id": "girl-summer",
            "image": "girl_summer.jpg",
            "title": "爽やか半袖コーデ",
            "description": "半袖シャツで涼しく、清潔感のある定番スタイル。",
            "tags": ["半袖シャツ", "リボン", "夏スカート"],
            "temp": "26°C以上",
            "rating": "4.9",
            "kind": "summer",
        },
        {
            "id": "girl-vest",
            "image": "girl_vest.jpg",
            "title": "ベストで調整コーデ",
            "description": "朝晩の気温差や冷房に対応しやすい万能コーデ。",
            "tags": ["長袖シャツ", "ニットベスト", "スカート"],
            "temp": "20〜25°C",
            "rating": "4.8",
            "kind": "vest",
        },
        {
            "id": "girl-cardigan",
            "image": "girl_cardigan.jpg",
            "title": "カーデで安心コーデ",
            "description": "肌寒い日も柔らかく暖かく。脱ぎ着もしやすいスタイル。",
            "tags": ["長袖シャツ", "カーディガン", "スカート"],
            "temp": "19°C以下",
            "rating": "4.8",
            "kind": "blazer",
        },
    ],
    "boys": [
        {
            "id": "boy-summer",
            "image": "boy_summer.jpg",
            "title": "爽やか半袖コーデ",
            "description": "半袖シャツで清潔感のある爽やかコーデ。暑い日も動きやすい。",
            "tags": ["半袖シャツ", "夏スラックス", "ベルト"],
            "temp": "26°C以上",
            "rating": "4.9",
            "kind": "summer",
        },
        {
            "id": "boy-vest",
            "image": "boy_vest.jpg",
            "title": "ベストでスマートコーデ",
            "description": "ベストで体温調整しながら、きちんと感も出せるスタイル。",
            "tags": ["長袖シャツ", "ニットベスト", "ネクタイ"],
            "temp": "20〜25°C",
            "rating": "4.8",
            "kind": "vest",
        },
        {
            "id": "boy-blazer",
            "image": "boy_blazer.jpg",
            "title": "ブレザーできちんとコーデ",
            "description": "風や冷えを防ぎながら、落ち着いた印象に仕上げるスタイル。",
            "tags": ["長袖シャツ", "ブレザー", "ネクタイ"],
            "temp": "19°C以下",
            "rating": "4.9",
            "kind": "blazer",
        },
    ],
}


def geocode_city(city_name: str) -> dict[str, Any] | None:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 1,
        "language": "ja",
        "format": "json",
        "countryCode": "JP",
    }
    response = requests.get(url, params=params, timeout=8)
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        return None

    item = results[0]
    admin1 = item.get("admin1") or ""
    name = item.get("name") or city_name
    return {
        "name": f"{admin1} {name}".strip(),
        "latitude": float(item["latitude"]),
        "longitude": float(item["longitude"]),
    }


def fetch_weather(latitude: float, longitude: float) -> dict[str, Any]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "weather_code",
            "precipitation",
            "wind_speed_10m",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "precipitation_probability",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
        ]),
        "timezone": "Asia/Tokyo",
        "forecast_days": 7,
    }
    response = requests.get(url, params=params, timeout=8)
    response.raise_for_status()
    return response.json()


def demo_weather() -> dict[str, Any]:
    now = datetime.now()
    days = [f"2026-09-{3+i:02d}" for i in range(7)]
    hours = [f"2026-09-03T{h:02d}:00" for h in range(24)]
    return {
        "current": {
            "time": now.isoformat(timespec="minutes"),
            "temperature_2m": 24.0,
            "apparent_temperature": 25.0,
            "relative_humidity_2m": 87,
            "weather_code": 61,
            "precipitation": 0.7,
            "wind_speed_10m": 3.0,
        },
        "hourly": {
            "time": hours,
            "temperature_2m": [23,23,22,22,22,22,23,24,24,25,25,26,26,27,27,27,26,26,25,25,24,24,24,23],
            "precipitation_probability": [80,80,75,70,65,60,70,80,90,100,100,90,80,70,60,50,45,40,35,30,30,25,20,20],
        },
        "daily": {
            "time": days,
            "weather_code": [61,2,1,3,61,0,2],
            "temperature_2m_max": [27,28,30,25,23,29,27],
            "temperature_2m_min": [24,22,23,20,19,21,22],
            "precipitation_probability_max": [100,30,10,20,80,10,20],
        },
    }


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
        rows.append("風が強め。体感温度が下がりやすいので上着があると安心。")
    return rows


def serialize_outfits(recommended_kind: str) -> dict[str, list[dict[str, Any]]]:
    result = {}
    for gender, rows in OUTFIT_LIBRARY.items():
        result[gender] = []
        for row in rows:
            item = dict(row)
            item["recommended"] = item["kind"] == recommended_kind
            result[gender].append(item)
    return result


@app.route("/")
def index():
    city_query = request.args.get("city", "").strip()
    demo = request.args.get("demo") == "1"

    city_name = DEFAULT_CITY
    latitude = DEFAULT_LAT
    longitude = DEFAULT_LON
    notice = None

    if city_query:
        try:
            place = geocode_city(city_query)
            if place:
                city_name = place["name"]
                latitude = place["latitude"]
                longitude = place["longitude"]
            else:
                notice = f"「{city_query}」が見つからなかったため、大阪市を表示しています。"
        except requests.RequestException:
            notice = "地域検索に接続できなかったため、大阪市を表示しています。"

    try:
        raw = demo_weather() if demo else fetch_weather(latitude, longitude)
    except requests.RequestException:
        raw = demo_weather()
        notice = "天気APIに接続できなかったため、デモ天気を表示しています。"

    current = raw["current"]
    daily = raw["daily"]
    hourly = raw["hourly"]

    temp = round(float(current["temperature_2m"]), 1)
    apparent = round(float(current["apparent_temperature"]), 1)
    humidity = int(round(float(current["relative_humidity_2m"])))
    wind = round(float(current["wind_speed_10m"]), 1)
    code = int(current["weather_code"])
    weather_label, weather_icon = WEATHER_META.get(code, ("天気", "cloud-sun"))

    rain_prob = int(daily["precipitation_probability_max"][0] or 0)
    max_temp = round(float(daily["temperature_2m_max"][0]), 1)
    min_temp = round(float(daily["temperature_2m_min"][0]), 1)

    recommended_kind = outfit_kind(temp, rain_prob, wind)
    outfits = serialize_outfits(recommended_kind)

    current_time = current.get("time", "")
    start_idx = hourly["time"].index(current_time) if current_time in hourly["time"] else 0
    hourly_times = hourly["time"][start_idx:start_idx + 12]
    hourly_temps = hourly["temperature_2m"][start_idx:start_idx + 12]
    hourly_rain = hourly["precipitation_probability"][start_idx:start_idx + 12]

    chart = {
        "labels": [t[-5:] for t in hourly_times],
        "temps": [round(float(v), 1) for v in hourly_temps],
        "rain": [int(v or 0) for v in hourly_rain],
    }

    week = []
    for i, date in enumerate(daily["time"][:7]):
        dcode = int(daily["weather_code"][i])
        dlabel, dicon = WEATHER_META.get(dcode, ("天気", "cloud-sun"))
        day_rain = int(daily["precipitation_probability_max"][i] or 0)
        day_max = float(daily["temperature_2m_max"][i])
        week.append({
            "date": date,
            "label": dlabel,
            "icon": dicon,
            "max": round(day_max),
            "min": round(float(daily["temperature_2m_min"][i])),
            "rain": day_rain,
            "kind": outfit_kind(day_max, day_rain, wind),
        })

    weather = {
        "temp": temp,
        "apparent": apparent,
        "humidity": humidity,
        "wind": wind,
        "label": weather_label,
        "icon": weather_icon,
        "rain_probability": rain_prob,
        "max": max_temp,
        "min": min_temp,
        "updated": current.get("time", "").replace("T", " "),
    }

    return render_template(
        "index.html",
        city_name=city_name,
        city_query=city_query,
        weather=weather,
        outfits=outfits,
        chart=chart,
        week=week,
        advice=day_advice(temp, rain_prob, wind),
        recommended_kind=recommended_kind,
        notice=notice,
    )


if __name__ == "__main__":
    app.run(debug=True)
