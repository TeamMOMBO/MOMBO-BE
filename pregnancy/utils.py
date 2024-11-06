from datetime import datetime, timezone
from dateutil import parser

def weeks_since(date_str):
    # ISO 8601 형식의 문자열을 datetime 객체로 변환
    input_date = parser.parse(date_str)
    # 현재 날짜를 오프셋-어웨어 객체로 변환
    today = datetime.now(timezone.utc)
    # 경과한 일수 계산
    delta_days = (today - input_date).days
    # 주차 계산 (일수를 7로 나누어 몇 주가 지났는지 확인)
    weeks_passed = delta_days // 7
    return weeks_passed + 1