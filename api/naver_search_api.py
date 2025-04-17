import requests
import os
from dotenv import load_dotenv

# .env 불러오기
load_dotenv()

# 요청 헤더
header = {
    # 호스트
    "Host": "openapi.naver.com",
    # User-Agent
    "User-Agent": os.getenv("USER_AGENT"),
    # 네이버 검색 Client ID
    "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
    # 네이버 검색 Client Secret
    "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET")
}

def searchAddress(name="동국대학교"):
    query = {
        # 쿼리 ( String )
        "query": name, 
        # 표시할 검색 결과 갯수 ( Integer )
        "display": 1
    }
    
    # 네이버 검색 API GET 요청
    res = requests.get(os.getenv("SEARCH_URL"),
                       headers=header,
                       params=query)
    
    # 요청 성공
    if res.ok:
        print(res.json())
        return res.json()['items'][0]['roadAddress']
    # 요청 실패
    else:
        print(f"Error : {res}")
        
# 디버깅용 메인 함수
def main():
    name = "동국대학교"
    searchAddress(name)
    
if __name__ == "__main__":
    main()