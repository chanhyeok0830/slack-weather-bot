import os
import requests
from datetime import datetime, timezone, timedelta

# 환경변수에서 로드
OWM_KEY      = os.getenv("OPENWEATHER_API_KEY")
SLACK_TOKEN  = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL= os.getenv("SLACK_CHANNEL_ID")

# (1) 위치 설정: 춘천
LAT, LON = 37.8813, 127.7299

# (2) 오늘 날짜 기준 UNIX timestamp (00:00 KST)
today = datetime.now(timezone(timedelta(hours=9))).replace(hour=0, minute=0, second=0)
date_str = today.date()

# (3) One Call 2.5 일반 예보 API 호출 (무료 플랜용)
url = (
    f"https://api.openweathermap.org/data/2.5/onecall"
    f"?lat={LAT}&lon={LON}"
    f"&exclude=minutely,hourly,alerts"
    f"&appid={OWM_KEY}&units=metric"
)
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

# (4) 오늘(daily[0]) 정보 추출
today_forecast = data["daily"][0]
min_temp     = today_forecast["temp"]["min"]
max_temp     = today_forecast["temp"]["max"]
precip       = today_forecast.get("pop", 0) * 100        # 강수확률 (%)
uv           = today_forecast.get("uvi", data["current"]["uvi"])
humidity     = today_forecast.get("humidity", data["current"]["humidity"])
weather_desc = today_forecast["weather"][0]["description"]

# (5) Slack 메시지 포맷
text = (
    f"*오늘의 날씨* ({date_str})\n"
    f"> 날씨: {weather_desc}\n"
    f"> 최고기온: {max_temp:.1f}°C  최저기온: {min_temp:.1f}°C\n"
    f"> 강수확률: {precip:.0f}%\n"
    f"> 자외선지수(UV): {uv:.1f}\n"
    f"> 습도: {humidity}%"
)

# (6) Slack API로 전송
slack_url = "https://slack.com/api/chat.postMessage"
headers   = {"Authorization": f"Bearer {SLACK_TOKEN}"}
payload   = {
    "channel": SLACK_CHANNEL,
    "text": text,
    "mrkdwn": True
}
r = requests.post(slack_url, json=payload, headers=headers)
r.raise_for_status()
print("오늘의 날씨를 성공적으로 전송했습니다.")
