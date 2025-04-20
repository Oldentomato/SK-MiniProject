import requests
import os
from dotenv import load_dotenv
from . import naver_search_api as na
# import naver_search_api as na
import re

load_dotenv()

def mapXY(input="동국대학교"):
    # 요청 헤더
    request_header = {
        'Accept': 'application/json',
        'X-NCP-APIGW-API-KEY-ID': os.getenv("NAVER_CLOUD_CLIENT"),
        'X-NCP-APIGW-API-KEY': os.getenv("NAVER_CLOUD_SECRET")
    }
    
    cleaned_input = input.strip()
    
    # 주소 패턴 정의
    # 도로명 주소 패턴
    road_addr_pattern = re.compile(r'\b\S+(?:로|길)\s+\d+(?:-\d+)?\b')
    # 지번 주소 패턴
    jibun_addr_pattern = re.compile(r'\b\S+(?:동|리)\s+\d+(?:-\d+)?\b')
    is_road_address = road_addr_pattern.search(cleaned_input)
    is_jibun_address = jibun_addr_pattern.search(cleaned_input)
    
    # 입력값이 지번주소나 도로명 주소인지 확인
    if is_road_address:
        adr = cleaned_input
    elif is_jibun_address:
        # "울산시 남구 무거동 산 622-15" 형식일 경우 " 산 " 제거
        adr = re.sub(r'\s산\s', ' ', cleaned_input, count=1)
    else:
        adr = na.searchAddress(input)
    
    # 요청 쿼리
    request_query = {
        "query" : adr,
    }

    # API 호출
    res = requests.get(os.getenv("MAPS_URL"),
                    headers=request_header,
                    params=request_query)

    if res.ok:        
        # 데이터 출력
        data = res.json()
        
        # 위도와 경도 값 확인
        if 'addresses' in data and len(data['addresses']) > 0 and 'y' in data['addresses'][0] and 'x' in data['addresses'][0]:
            # 위도
            m_lat = data['addresses'][0]['y']
            # 경도
            m_lng = data['addresses'][0]['x']
        else:
            return { "errorMessage": "검색 결과 없음" }
    
        return {
            "시도": data['addresses'][0]["addressElements"][0]["longName"],
            '자치구명': data['addresses'][0]["addressElements"][1]["longName"],
            '법적동명': data['addresses'][0]["addressElements"][2]["longName"],
            '도로명주소' : data['addresses'][0]["roadAddress"],
            '지번주소': data['addresses'][0]["jibunAddress"],
            "위도" : m_lat,
            "경도" : m_lng
        }
    else:
        print(f'Error: {res.url}')


# 디버깅용 메인 함수
def main():
    rst = mapXY(input="서울시 중구 필동3가 39-31")
    
if __name__ == "__main__":
    main()