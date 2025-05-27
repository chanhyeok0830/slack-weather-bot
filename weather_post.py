import requests
from datetime import datetime, timezone, timedelta

# → 테스트용 하드코딩된 키 (앞뒤 공백 주의!)
API_KEY = "dc808aaafd0c36d73c8652db8190fa69"
LAT, LON = 37.8813, 127.7299

def fetch_weather_free_direct():
    today = datetime.now(timezone(timedelta(hours=9))).date()

    # 1) 현재 날씨
    url1 = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}"
        f"&appid={API_KEY}"
        f"&units=metric"
    )
    print(f"[Current] URL: {url1}")
    resp1 = requests.get(url1)
    print(f"[Current] HTTP {resp1.status_code}, Body: {resp1.text}")
    resp1.raise_for_status()
    curr = resp1.json()

    # 2) 5일 예보
    url2 = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={LAT}&lon={LON}"
        f"&appid={API_KEY}"
        f"&units=metric"
    )
    print(f"[Forecast] URL: {url2}")
    resp2 = requests.get(url2)
    print(f"[Forecast] HTTP {resp2.status_code}, Body(sample): {resp2.text[:200]}")
    resp2.raise_for_status()
    forecast = resp2.json()

    # 3) 오늘 데이터 필터링
    temps, pops = [], []
    for item in forecast.get("list", []):
        dt = datetime.fromtimestamp(item["dt"], timezone(timedelta(hours=9)))
        if dt.date() == today:
            temps.append(item["main"]["temp"])
            pops.append(item.get("pop", 0))

    print(f"Collected {len(temps)} data points for today.")
    if not temps:
        raise RuntimeError("오늘 예보 데이터가 없습니다.")

    info = {
        "date": today,
        "weather": curr["weather"][0]["description"],
        "min_temp": min(temps),
        "max_temp": max(temps),
        "precip": max(pops)*100,
        "humidity": curr["main"]["humidity"],
        # UV 정보는 Current API에 없음
        "uv": None,
    }
    return info

if __name__ == "__main__":
    info = fetch_weather_free_direct()
    print("===== 오늘의 날씨 =====")
    print(f"날짜       : {info['date']}")
    print(f"날씨       : {info['weather']}")
    print(f"최저기온    : {info['min_temp']:.1f}°C")
    print(f"최고기온    : {info['max_temp']:.1f}°C")
    print(f"강수확률    : {info['precip']:.0f}%")
    print(f"습도       : {info['humidity']}%")
    print(f"자외선 지수 : {info['uv'] or '지원 안됨'}")
