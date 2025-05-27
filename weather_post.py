import os
import requests
from datetime import datetime, timezone, timedelta

def debug_env():
    print("=== ENVIRONMENT VARIABLES ===")
    print(f"OPENWEATHER_API_KEY loaded: {'YES' if os.getenv('OPENWEATHER_API_KEY') else 'NO'}")
    print(f"SLACK_BOT_TOKEN   loaded: {'YES' if os.getenv('SLACK_BOT_TOKEN') else 'NO'}")
    print(f"SLACK_CHANNEL_ID  loaded: {'YES' if os.getenv('SLACK_CHANNEL_ID') else 'NO'}")
    print("=============================\n")

def fetch_weather_free():
    LAT, LON = 37.8813, 127.7299
    today = datetime.now(timezone(timedelta(hours=9))).date()

    # 1) 현재 날씨 조회
    url1 = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        f"&units=metric"
    )
    print(f"[Weather][Current] URL: {url1}")
    resp1 = requests.get(url1)
    print(f"[Weather][Current] HTTP {resp1.status_code}, Body: {resp1.text}")
    resp1.raise_for_status()
    curr = resp1.json()

    # 2) 5일 예보 조회
    url2 = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        f"&units=metric"
    )
    print(f"[Weather][Forecast] URL: {url2}")
    resp2 = requests.get(url2)
    print(f"[Weather][Forecast] HTTP {resp2.status_code}, Body(sample): {resp2.text[:500]}")
    resp2.raise_for_status()
    forecast = resp2.json()

    # 3) 오늘 날짜(today) 기준으로 list에서 온도·강수 확률 모으기
    temps = []
    pops  = []
    for item in forecast.get("list", []):
        dt = datetime.fromtimestamp(item["dt"], timezone(timedelta(hours=9)))
        if dt.date() == today:
            temps.append(item["main"]["temp"])
            pops.append(item.get("pop", 0))

    if not temps:
        raise RuntimeError("오늘 예보 데이터가 없습니다.")

    min_temp = min(temps)
    max_temp = max(temps)
    precip   = max(pops) * 100  # %

    # 4) 자외선 지수(UV)는 current 에서 못 가져옴 → 0으로 대체하거나 다른 서비스 필요
    uv = curr.get("uvi", 0)

    return {
        "weather_desc": curr["weather"][0]["description"],
        "min_temp": min_temp,
        "max_temp": max_temp,
        "precip": precip,
        "uv": uv,
        "humidity": curr["main"]["humidity"],
        "date_str": today,
    }

def post_to_slack(info):
    text = (
        f"*오늘의 날씨* ({info['date_str']})\n"
        f"> 날씨: {info['weather_desc']}\n"
        f"> 최고기온: {info['max_temp']:.1f}°C  최저기온: {info['min_temp']:.1f}°C\n"
        f"> 강수확률: {info['precip']:.0f}%\n"
        f"> 자외선지수(UV): {info['uv']:.1f}\n"
        f"> 습도: {info['humidity']}%"
    )

    slack_url = "https://slack.com/api/chat.postMessage"
    headers   = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
    payload   = {
        "channel": os.getenv("SLACK_CHANNEL_ID"),
        "text": text,
        "mrkdwn": True
    }

    print(f"[Slack] Posting to {payload['channel']}")
    print(f"[Slack] Message:\n{text}")
    resp = requests.post(slack_url, json=payload, headers=headers)
    print(f"[Slack] HTTP {resp.status_code}, Body: {resp.text}")
    resp.raise_for_status()

def main():
    debug_env()

    try:
        info = fetch_weather_free()
    except Exception as e:
        print(f"[ERROR] fetch_weather_free(): {e}")
        return

    try:
        post_to_slack(info)
    except Exception as e:
        print(f"[ERROR] post_to_slack(): {e}")
        return

    print("[Main] Done.")

if __name__ == "__main__":
    main()
