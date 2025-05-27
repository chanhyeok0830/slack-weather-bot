import os
import requests
from datetime import datetime, timezone, timedelta

def debug_env():
    print("=== ENVIRONMENT VARIABLES ===")
    print(f"OPENWEATHER_API_KEY loaded: {'YES' if os.getenv('OPENWEATHER_API_KEY') else 'NO'}")
    print(f"SLACK_BOT_TOKEN loaded: {'YES' if os.getenv('SLACK_BOT_TOKEN') else 'NO'}")
    print(f"SLACK_CHANNEL_ID loaded: {'YES' if os.getenv('SLACK_CHANNEL_ID') else 'NO'}")
    print("=============================\n")

def fetch_weather():
    # (1) 위치 설정: 춘천
    LAT, LON = 37.8813, 127.7299

    # (2) 오늘 날짜(00:00 KST)
    today = datetime.now(timezone(timedelta(hours=9))).replace(hour=0, minute=0, second=0)
    date_str = today.date()

    # (3) One Call 2.5 API URL 구성
    url = (
        f"https://api.openweathermap.org/data/2.5/onecall"
        f"?lat={LAT}&lon={LON}"
        f"&exclude=minutely,hourly,alerts"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        f"&units=metric"
    )
    print(f"[Weather] Request URL: {url}")

    try:
        resp = requests.get(url)
        print(f"[Weather] HTTP status: {resp.status_code}")
        print(f"[Weather] Response body:\n{resp.text[:500]}")  # 앞 500자만 출력
        resp.raise_for_status()
    except Exception as e:
        print(f"[Weather][ERROR] Exception during weather fetch: {e}")
        raise

    data = resp.json()
    today_forecast = data.get("daily", [None])[0]
    if not today_forecast:
        print("[Weather][ERROR] 'daily' 데이터 없음:", data)
        raise RuntimeError("Weather data missing 'daily'")

    # (4) 데이터 추출
    min_temp     = today_forecast["temp"]["min"]
    max_temp     = today_forecast["temp"]["max"]
    precip       = today_forecast.get("pop", 0) * 100
    uv           = today_forecast.get("uvi", data.get("current", {}).get("uvi"))
    humidity     = today_forecast.get("humidity", data.get("current", {}).get("humidity"))
    weather_desc = today_forecast["weather"][0]["description"]

    return date_str, weather_desc, min_temp, max_temp, precip, uv, humidity

def post_to_slack(date_str, weather_desc, min_temp, max_temp, precip, uv, humidity):
    text = (
        f"*오늘의 날씨* ({date_str})\n"
        f"> 날씨: {weather_desc}\n"
        f"> 최고기온: {max_temp:.1f}°C  최저기온: {min_temp:.1f}°C\n"
        f"> 강수확률: {precip:.0f}%\n"
        f"> 자외선지수(UV): {uv:.1f}\n"
        f"> 습도: {humidity}%"
    )

    slack_url = "https://slack.com/api/chat.postMessage"
    headers   = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
    payload   = {
        "channel": os.getenv("SLACK_CHANNEL_ID"),
        "text": text,
        "mrkdwn": True
    }

    print(f"[Slack] Posting to channel: {payload['channel']}")
    print(f"[Slack] Payload:\n{text}")

    try:
        resp = requests.post(slack_url, json=payload, headers=headers)
        print(f"[Slack] HTTP status: {resp.status_code}")
        print(f"[Slack] Response body:\n{resp.text}")
        resp.raise_for_status()
    except Exception as e:
        print(f"[Slack][ERROR] Exception during Slack post: {e}")
        raise

def main():
    debug_env()

    try:
        date_str, weather_desc, min_temp, max_temp, precip, uv, humidity = fetch_weather()
    except Exception:
        print("[Main][ERROR] fetch_weather() failed")
        return

    try:
        post_to_slack(date_str, weather_desc, min_temp, max_temp, precip, uv, humidity)
    except Exception:
        print("[Main][ERROR] post_to_slack() failed")
        return

    print("[Main] Done.")

if __name__ == "__main__":
    main()
