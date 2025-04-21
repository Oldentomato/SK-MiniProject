import requests
import os
from dotenv import load_dotenv

load_dotenv()

def roadAddressConvertor(jibun_address):
    request_header = {
        'confmKey': os.getenv("ROAD_ADDRESS_API_KEY"),
        'currentPage' : '1',
        'countPerPage' : '1',
        'keyword' : jibun_address,
        'resultType' : 'json',
        'hstryYn' : 'N'
    }
    
    # API 호출
    res = requests.get(os.getenv("ROAD_ADDRESS_URL"),
                    params=request_header)
    
    if res.ok:
        # print(res.json())
        data=res.json()
        if 'results' in data and 'juso' in data['results'] and len(data['results']['juso']) > 0:
            return data['results']['juso'][0]['roadAddrPart1']
        else:
            return None
        
    else:
        print(f"Error : {jibun_address} 주소 변환 실패")
        return None
        
        
def main():
    jibun_address = "동국대학교"
    result = roadAddressConvertor(jibun_address)
    print(result)
        
if __name__ == "__main__":
    main()
        