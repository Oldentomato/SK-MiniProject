from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException # TimeoutException 임포트

from urllib.parse import urljoin
# 위도 경도
from naver_api import naver_map_api as na

# 다방 base url
dabang_url ="https://www.dabangapp.com/map/"

# 타입 딕셔너리
bang_dict = {
    "원룸/투룸" : "onetwo",
    "아파트" : "apt",
    "주택빌라" : "house",
    "오피스텔" : "officetel"
}

# 크롬 옵션
chrome_options = Options()
chrome_options.add_argument('--headless')  # 화면 표시 없이 실행
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

def getDabangList(search_item, bang_type="원룸/투룸"):
    if bang_type not in bang_dict.keys():
        return {
            "errorMessage": "방 형식이 올바르지 않습니다."
        }
    
    # 최종 url
    request_url = urljoin(dabang_url, bang_dict[bang_type])

    # 위도 경도 계산
    xy_info = na.mapXY(search_item)

    # 쿼리
    query = "?m_lat={}&m_lng={}&m_zoom=18".format(xy_info["위도"], xy_info["경도"])

    # 요청 url
    request_url = urljoin(request_url, query)

    print("요청 url : ", request_url)

    driver = webdriver.Chrome(options=chrome_options)

    t_dict = {
        "원룸/투룸" : "onetwo-list",
        "아파트"  : "apt-list",
        "주택빌라" : "house-list",
        "오피스텔" : "officetel-list"
    }

    driver.get(request_url)

    # 찾으려는 요소의 CSS 선택자
    div_selector = f"div#{t_dict[bang_type]} > div"
    wait_timeout = 3        # 최대 대기 시간
    ul_wait_timeout = 3     # ul 요소 대기 시간

    try:

        # WebDriverWait 객체 생성
        wait = WebDriverWait(driver, wait_timeout)

        # 지정한 CSS 선택자를 가진 요소가 DOM에 나타날 때까지 대기
        # visibility_of_element_located: 요소가 DOM에 존재하고 화면에 보일 때 통과
        div_element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, div_selector))
        )

        # 찾은 div 요소 내부에서 ul 요소 기다리기
        # WebDriverWait의 첫 번째 인자로 WebElement(div_element)를 전달하면 그 하위에서만 검색
        ul_element = WebDriverWait(div_element, ul_wait_timeout).until(
            # EC.presence_of_element_located((By.TAG_NAME, "ul"))
            EC.visibility_of_element_located((By.TAG_NAME, "ul"))
        )
        
        # 매물 리스트
        bang_list = []
        
        li_elements = ul_element.find_elements(By.TAG_NAME, "li")
        if li_elements:
            # 가져온 li 요소들 처리 
            for index, li in enumerate(li_elements):
                # 매물 한개 데이터
                bang_info = {
                    '사이트': '다방',
                    '시도': xy_info['시도'],
                    '자치구명': xy_info['자치구명'],
                    '법정동명': xy_info['법정동명'],
                }
                # li 에 있는 2개의 div 가져오기
                div_elements = li.find_elements(By.TAG_NAME, "div")
                
                # 이미지 가져오기
                img_element = li.find_element(By.CSS_SELECTOR, "img")
                img_url = img_element.get_attribute('data-src')
                
                bang_info["이미지"] = img_url
                
                if div_elements:                
                    # [ 월세, 보증금/월세, 방식, 층, 면적, 관리비, 안내사항 ]
                    details = div_elements[3].text.split('\n')
                    
                    # '월세 3000/65' or '전세 5000' 
                    # 방식
                    bang_info["방식"] = details[0].split(' ')[0].strip()
                    if bang_info["방식"] == "월세":
                        money_info = details[0].split(' ')[1].split('/')
                        bang_info["보증금"] = money_info[0]
                        bang_info["월세"] = money_info[1]
                    elif bang_info["방식"] == "전세":
                        bang_info["전세금"] = details[0].split(' ')[1]
                    else:
                        bang_info["매매금"] = details[0].split(' ')[1]
                    
                    # 방 종류 ( 원룸, 투룸 등 )
                    bang_info["방_종류"] = details[1]
                    
                    # ( '2층, 19.82m², 관리비 5만' )
                    # 층수 
                    bang_info["층"] = details[2].split(', ')[0].strip()
                    # 임대면적 ( 26.44m² )
                    bang_info["임대면적"] = details[2].split(', ')[1].split('m')[0].strip()
                    # 관리비
                    bang_info["관리비"] = details[2].split(', ')[2].split(' ')[1].replace('만', '')
                    
                bang_list.append(bang_info) 
        
        return bang_list
                    
    # TimeoutException: 지정된 시간 내에 요소를 찾지 못하면 발생
    except TimeoutException:
        return {
            "errorMessage" : "검색한 위치 근처 매물이 없습니다."
        }

    except Exception as e:
        return {
            "errorMessage" : e
        }
    finally:
        driver.quit()
        
def main():
    rst = getDabangList("동국대")
    print(rst)

if __name__ == "__main__":
    main()