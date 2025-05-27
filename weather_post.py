import os
import requests
from datetime import datetime, timezone, timedelta

# 환경변수에서 로드
OWM_KEY = os.getenv("OPENWEATHER_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL_ID")

# (1) 위치 설정: 춘천
LAT, LON = 37.8813, 127.7299

# (2) 오늘 날짜 기준 UNIX timestamp (00:00)
today = datetime.now(timezone(timedelta(hours=9))).replace(hour=0, minute=0, second=0)
dt = int(today.timestamp())

# (3) OpenWeatherMap One Call Timemachine API 호출
url = (
    f"https://api.openweathermap.org/data/3.0/onecall/timemachine"
    f"?lat={LAT}&lon={LON}&dt={dt}&appid={OWM_KEY}&units=metric"
)
resp = requests.get(url)
resp.raise_for_status()
data = resp.json()

# (4) 필요한 정보 추출
temps = [hour["temp"] for hour in data["hourly"]]
min_temp, max_temp = min(temps), max(temps)
# 강수확률은 hourly[].pop(rain,0)["rain"]이 아니라, pop(populated) 하는 게 API마다 다름
precip = max(h.get("pop", 0) for h in data["hourly"]) * 100  # %
# UV, 습도는 current에서
uv = data["current"]["uvi"]
humidity = data["current"]["humidity"]
weather_desc = data["current"]["weather"][0]["description"]

# (5) Slack 메시지 포맷
text = (
    f"*오늘의 날씨* ({today.date()})\n"
    f"> 날씨: {weather_desc}\n"
    f"> 최고기온: {max_temp:.1f}°C  최저기온: {min_temp:.1f}°C\n"
    f"> 강수확률: {precip:.0f}%\n"
    f"> 자외선지수(UV): {uv:.1f}\n"
    f"> 습도: {humidity}%"
)

# (6) Slack API로 전송
slack_url = "https://slack.com/api/chat.postMessage"
headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
payload = {
    "channel": SLACK_CHANNEL,
    "text": text,
    "mrkdwn": True
}
r = requests.post(slack_url, json=payload, headers=headers)
r.raise_for_status()
