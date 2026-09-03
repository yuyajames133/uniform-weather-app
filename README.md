# 今日の制服コーデ v2

Open-Meteoの天気に連動して、女子・男子の高校制服コーデを提案するFlaskアプリです。

## Macで起動

```bash
cd uniform_weather_app_v2
python3 -m pip install -r requirements.txt
python3 app.py
```

ブラウザ:
`http://127.0.0.1:5000`

APIを使わずUIだけ確認:
`http://127.0.0.1:5000/?demo=1`

## Render
Build Command:
`pip install -r requirements.txt`

Start Command:
`gunicorn app:app`

## 使用
- Open-Meteo Forecast API
- Open-Meteo Geocoding API
- Chart.js
- Lucide Icons
- ローカル同梱の制服ビジュアル画像
