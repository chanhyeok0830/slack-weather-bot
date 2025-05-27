import os
import requests
from datetime import datetime, timezone, timedelta

def debug_env():
    print("=== ENVIRONMENT VARIABLES ===")
    print(f"OPENWEATHER_API_KEY loaded: {'YES' if os.getenv('OPENWEATHER_API_KEY') else 'NO'}")
    print(f"SLACK_BOT_TOKEN   loaded: {'YES' if os.getenv('SLACK_BOT_TOKEN') else 'NO'}")
    print(f"SLACK_CHANNEL_ID  loaded: {'YES' if os.getenv('SLACK_CHANNEL_ID') else 'NO'}")
    print("=============================\n")

def fetch_today_weather():
    LAT, LON = 37.8813, 127.7299
    today = datetime.now(timezone(timedelta(hours=9))).date()
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        f"&units=metric"
    )
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return {
        "date_str": today,
        "weather": data["weather"][0]["description"],
        "temp": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
    }

def post_to_slack(info):
    lines = [
        f"*오늘의 날씨* ({info['date_str']})",
        f"> 날씨: {info['weather']}",
        f"> 기온: {info['temp']:.1f}°C  (체감: {info['feels_like']:.1f}°C)",
        f"> 습도: {info['humidity']}%"
    ]
    text = "\n".join(lines)

    slack_url = "https://slack.com/api/chat.postMessage"
    headers   = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
    payload   = {
        "channel": os.getenv("SLACK_CHANNEL_ID"),
        "text": text,
        "mrkdwn": True
    }

    print(f"[Slack] POST {slack_url}")
    print(f"[Slack] headers: {headers}")
    print(f"[Slack] payload: {payload}")
    resp = requests.post(slack_url, json=payload, headers=headers)
    print(f"[Slack] HTTP {resp.status_code}")
    print(f"[Slack] response body: {resp.text}")
    # Slack이 ok:false 를 반환하면 raise_for_status()는 동작하지 않으므로,
    # 직접 확인해보고 싶으면 아래 주석을 해제하세요.
    # data = resp.json()
    # if not data.get("ok", False):
    #     raise RuntimeError(f"Slack API error: {data}")

    resp.raise_for_status()

def main():
    debug_env()
    try:
        info = fetch_today_weather()
    except Exception as e:
        print(f"[ERROR] fetch_today_weather(): {e}")
        return

    try:
        post_to_slack(info)
    except Exception as e:
        print(f"[ERROR] post_to_slack(): {e}")
        return

    print("[Main] Done.")

if __name__ == "__main__":
    main()
