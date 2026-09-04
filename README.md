# 今日の制服コーデ - Mobile Edition

完全スマホ専用版です。

## 特徴
- 430px以下を前提にしたスマホUI
- 今日の天気をコンパクト表示
- 男子 / 女子をワンタップ切替
- 気温・雨・風から自動判定した「今日のBEST」だけを大きく表示
- 実画像アセット使用
- ほぼ1画面で今日必要な情報が完結
- Open-Meteo API
- Render Free Web Service対応

## ローカル起動
```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

## Render
Build:
`pip install -r requirements.txt`

Start:
`gunicorn app:app`
