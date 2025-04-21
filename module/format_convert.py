import numpy as np

# 층수 문자열 int로 치환
def floorFormat(s):
    if s == "고":
        return 10
    elif s == "중":
        return 5
    elif s == "저":
        return 3 
    elif s == "반지":
        return 1
    else:
        if "층" in s:
            return int(s.replace("층", ""))
        return int(s) 

# 한글 금액에서 숫자로 치환하는 함수
def korean_money_to_int(s):
    if s == np.nan:
        raise Exception("금액 누락")
    if s == "없음":
        return 0
    if int(float(str(s).replace(",", ""))) == 0:
        return 0
    if type(s) == int:
        return s
    s = str(s).replace(" ", "").replace(",", "").replace("원", "")

    result = 0
    units = {"억": 100000000, "천만": 10000000, "백만": 1000000, "만": 10000, "천": 1000, "백": 100}
    last_pos = 0
    for unit, value in units.items():
        if unit in s:
            parts = s.split(unit)
            num = parts[0][last_pos:]
            num = int(num) if num else 1
            result += num * value
            s = parts[1]
            last_pos = 0

    # 만약 나머지가 숫자라면 더하기
    if s.isdigit():
        result += int(s)

    return result