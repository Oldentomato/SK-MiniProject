import requests
import os
from dotenv import load_dotenv
from . import naver_search_api as na
# import naver_search_api as na

load_dotenv()

def mapXY(input="동국대학교"):
    # 요청 헤더
    request_header = {
        'Accept': 'application/json',
        'X-NCP-APIGW-API-KEY-ID': os.getenv("NAVER_CLOUD_CLIENT"),
        'X-NCP-APIGW-API-KEY': os.getenv("NAVER_CLOUD_SECRET")
    }
    
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
        
        # 위도
        m_lat = data['addresses'][0]['y']
        # 경도
        m_lng = data['addresses'][0]['x']
    
        return {
            "시도": data['addresses'][0]["addressElements"][0]["longName"],
            '자치구명': data['addresses'][0]["addressElements"][1]["longName"],
            '법정동명': data['addresses'][0]["addressElements"][2]["longName"],
            "위도" : m_lat,
            "경도" : m_lng
        }
    else:
        print(f'Error: {res.url}')


# 디버깅용 메인 함수
def main():
    rst = mapXY(input="동국대학교")
    print(rst)
    
if __name__ == "__main__":
    main()