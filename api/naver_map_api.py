import requests
import os
from dotenv import load_dotenv
from naver_search_api import searchAddress

load_dotenv()

def mapXY(input="동국대학교"):
    # 요청 헤더
    request_header = {
        'Accept': 'application/json',
        'X-NCP-APIGW-API-KEY-ID': os.getenv("NAVER_CLOUD_CLIENT"),
        'X-NCP-APIGW-API-KEY': os.getenv("NAVER_CLOUD_SECRET")
    }
    
    adr = searchAddress(input)
    
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
        
        print(f'위도 = {m_lat}\n경도 = {m_lng}')
        
    else:
        print(f'Error: {res.url}')

mapXY()