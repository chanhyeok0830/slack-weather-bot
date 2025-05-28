import os
import requests
import random
from datetime import datetime, timezone, timedelta

# ─── 1. 이모티콘 매핑 ─────────────────────────────────────────────────────────
EMOJI_MAP = {
    "맑음": "🌞",
    "구름": "☁️",
    "흐림": "☁️",
    "비": "☔",
    "눈": "❄️",
    "폭풍": "⛈️",
}

# ─── 2. 날씨별 자연어 템플릿 ───────────────────────────────────────────────────
TEMPLATES = {
    "맑음": [
        "오늘은 하루 종일 맑은 날씨가 예상돼요. ☀️",
        "하늘이 맑고 화창해요. 야외 활동하기 좋아요!",
    ],
    "구름": [
        "구름이 약간 끼겠지만 대체로 맑아요. ☁️",
        "오늘은 흐리지만 큰 비 없이 온화할 예정이에요.",
    ],
    "흐림": [
        "오늘은 전반적으로 흐린 날씨가 이어질 거예요.",
        "구름이 많아 해가 잘 보이지 않을 수 있어요.",
    ],
    "비": [
        "비가 내릴 수 있으니 우산 챙기세요. ☔",
        "비 소식이 있어요. 외출하실 때 우산 잊지 마세요!",
    ],
    "눈": [
        "눈 소식이 있어요. 따뜻하게 입으세요! ❄️",
        "눈이 올 수 있으니 주의하세요.",
    ],
    "폭풍": [
        "천둥과 번개를 동반한 비가 예상돼요. 주의하세요! ⛈️",
    ],
}
    
def select_emoji(desc):
    for key, emo in EMOJI_MAP.items():
        if key in desc:
            return emo
    return "🌈"

def select_template(desc):
    for key, tpl_list in TEMPLATES.items():
        if key in desc:
            return random.choice(tpl_list)
    # 기본 템플릿
    return f"{desc} 날씨입니다."

# ─── 3. 하루 전체 날씨 예보 분석 ─────────────────────────────────────────────
def analyze_daily_weather(forecasts):
    """하루 전체 예보를 분석해서 대표 날씨를 결정"""
    rain_count = 0
    snow_count = 0
    storm_count = 0
    cloudy_count = 0
    clear_count = 0
    
    rain_times = []  # 비 오는 시간대 저장
    total_pop = 0
    temp_sum = 0
    feels_sum = 0
    humidity_sum = 0
    count = len(forecasts)
    
    for forecast in forecasts:
        desc = forecast['weather'][0]['description'].lower()
        forecast_time = datetime.fromtimestamp(forecast['dt'], timezone(timedelta(hours=9)))
        hour = forecast_time.hour
        
        # 날씨 유형별 카운트
        if '비' in desc or 'rain' in desc:
            rain_count += 1
            rain_times.append(hour)
        elif '눈' in desc or 'snow' in desc:
            snow_count += 1
        elif '천둥' in desc or 'thunder' in desc or 'storm' in desc:
            storm_count += 1
        elif '흐림' in desc or '구름' in desc or 'cloud' in desc:
            cloudy_count += 1
        else:
            clear_count += 1
        
        # 평균값 계산용
        total_pop += forecast.get('pop', 0) * 100  # 강수확률은 0-1 범위
        temp_sum += forecast['main']['temp']
        feels_sum += forecast['main']['feels_like']
        humidity_sum += forecast['main']['humidity']
    
    # 대표 날씨 결정 (우선순위: 폭풍 > 눈 > 비 > 흐림 > 맑음)
    if storm_count > 0:
        main_weather = "폭풍"
    elif snow_count > 0:
        main_weather = "눈"
    elif rain_count > 0:
        main_weather = "비"
    elif cloudy_count > clear_count:
        main_weather = "흐림"
    else:
        main_weather = "맑음"
    
    # 비 오는 시간대를 사용자 친화적으로 변환
    rain_info = None
    if rain_times:
        if len(rain_times) == 1:
            rain_info = f"{rain_times[0]}시경"
        elif len(rain_times) == 2:
            rain_info = f"{rain_times[0]}시, {rain_times[1]}시경"
        else:
            # 연속된 시간대인지 확인
            rain_times.sort()
            if max(rain_times) - min(rain_times) <= 6:  # 6시간 이내 범위
                rain_info = f"{min(rain_times)}시~{max(rain_times)}시경"
            else:
                rain_info = f"하루 중 여러 시간대 ({len(rain_times)}회)"
    
    return {
        "main_weather": main_weather,
        "avg_temp": temp_sum / count,
        "avg_feels": feels_sum / count,
        "avg_humidity": humidity_sum / count,
        "max_pop": total_pop / count,  # 평균 강수확률
        "rain_info": rain_info
    }

def fetch_weather():
    LAT, LON = 37.8813, 127.7299
    today = datetime.now(timezone(timedelta(hours=9))).date()
    
    # 5일 예보 API (3시간 간격)
    url = (
        "https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        "&units=metric"
        "&lang=kr"
    )
    
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    
    # 오늘 날짜의 예보만 필터링
    today_forecasts = []
    today_str = today.strftime("%Y-%m-%d")
    
    for item in data['list']:
        forecast_time = datetime.fromtimestamp(item['dt'], timezone(timedelta(hours=9)))
        if forecast_time.date().strftime("%Y-%m-%d") == today_str:
            today_forecasts.append(item)
    
    # 현재 날씨도 가져오기 (현재 기온 정확도를 위해)
    current_url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={os.getenv('OPENWEATHER_API_KEY')}"
        "&units=metric"
        "&lang=kr"
    )
    current_r = requests.get(current_url)
    current_r.raise_for_status()
    current_data = current_r.json()
    
    # 하루 전체 날씨 분석
    if today_forecasts:
        analysis = analyze_daily_weather(today_forecasts)
        return {
            "date": today.strftime("%m월 %d일"),
            "desc": analysis["main_weather"],
            "temp": current_data["main"]["temp"],  # 현재 기온
            "feels": current_data["main"]["feels_like"],  # 현재 체감기온
            "humidity": analysis["avg_humidity"],
            "pop": analysis["max_pop"],
            "rain_info": analysis["rain_info"]
        }
    else:
        # 예보 데이터가 없으면 현재 날씨 사용
        return {
            "date": today.strftime("%m월 %d일"),
            "desc": current_data["weather"][0]["description"],
            "temp": current_data["main"]["temp"],
            "feels": current_data["main"]["feels_like"],
            "humidity": current_data["main"]["humidity"],
            "pop": 0,
            "rain_info": None
        }

# ─── 4. 슬랙 전송 ────────────────────────────────────────────────────────────
def post_to_slack(info):
    emoji = select_emoji(info["desc"])
    sentence = select_template(info["desc"])
    
    # 메시지 구성
    text_lines = [
        f"{emoji}",
        f"*오늘의 날씨* ({info['date']})",
        f"> {sentence}",
        f"> 기온: {info['temp']:.1f}°C  (체감: {info['feels']:.1f}°C)",
        f"> 습도: {info['humidity']:.0f}%",
        f"> 강수확률: {info['pop']:.0f}%"
    ]
    
    # 비 정보가 있으면 추가
    if info.get('rain_info'):
        text_lines.append(f"> 🌧️ 비 예상 시간대: {info['rain_info']}")
    
    text = "\n".join(text_lines)

    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"},
        json={
            "channel": os.getenv("SLACK_CHANNEL_ID"),
            "text": text,
            "mrkdwn": True,
            "icon_emoji": emoji,
        }
    )
    resp.raise_for_status()

def main():
    info = fetch_weather()
    post_to_slack(info)

if __name__ == "__main__":
    main()