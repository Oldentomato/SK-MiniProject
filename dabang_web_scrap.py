from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
# StaleElementReferenceException과 ElementClickInterceptedException도 임포트
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
from dotenv import load_dotenv
from urllib.parse import urljoin
import pandas as pd

# naver_api 임포트 가정
from naver_api import naver_map_api as na

load_dotenv()

# 다방 base url
dabang_url = "https://www.dabangapp.com/map/"

# 타입 딕셔너리
bang_dict = {
    "원룸/투룸": "onetwo",
    "아파트": "apt",
    "주택빌라": "house",
    "오피스텔": "officetel"
}

# 드라이버 생성 (WebDriverManager 사용 권장)
def load_driver():
    options = Options()
    # headless 사용 시 필요한 옵션들
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument(f'user-agent={os.getenv("USER_AGENT")}') # User-Agent 설정

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(1)
    return driver


def getDabangList(search_item, bang_type="원룸/투룸"):
    if bang_type not in bang_dict:
        return {"errorMessage": "방 형식이 올바르지 않습니다."}
    
    request_url = urljoin(dabang_url, bang_dict[bang_type])
    xy_info = na.mapXY(search_item)
    
    # 위치 오류
    if not xy_info or "위도" not in xy_info or "경도" not in xy_info:
        return {"errorMessage": f"'{search_item}'에 대한 위치 정보를 찾을 수 없습니다."}

    query = f"?m_lat={xy_info['위도']}&m_lng={xy_info['경도']}&m_zoom=17"
    request_url = urljoin(request_url, query)
    print("요청 url : ", request_url)

    driver = load_driver()
    wait_timeout = 10  # 대기 시간

    t_dict = {
        "원룸/투룸": "onetwo-list",
        "아파트": "apt-list",
        "주택빌라": "house-list",
        "오피스텔": "officetel-list"
    }
    
    list_container_selector = f"div#{t_dict[bang_type]}" # 목록 전체 컨테이너
    list_ul_selector = f"{list_container_selector} ul"  # ul 선택자
    list_li_selector = f"{list_ul_selector} > li"       # li 선택자 (XPath가 더 안정적일 수 있음)

    bang_list = []

    try:
        driver.get(request_url)

        # 목록 컨테이너(div)가 나타날 때까지 기다림
        wait = WebDriverWait(driver, wait_timeout)
        list_container_div = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, list_container_selector))
        )

        # ul 요소가 나타날 때까지 기다림
        ul_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, list_ul_selector))
            # EC.visibility_of_element_located((By.CSS_SELECTOR, list_ul_selector)) # 보이는 것까지 확인하려면
        )

        initial_li_elements = ul_element.find_elements(By.CSS_SELECTOR, list_li_selector.split(' > ')[1]) # ul 하위의 li만
        num_elements = len(initial_li_elements)
        print(f"총 {num_elements}개의 매물을 찾았습니다.")

        if num_elements == 0:
             return {"errorMessage": "검색된 매물이 없습니다."}

        # 매물 리스트 루프
        for index in range(num_elements):
            # 디버깅용
            # print(f"\n--- 매물 {index + 1}/{num_elements} 처리 시작 ---")
            try:
                # 매번 목록(ul)과 li를 다시 찾음
                current_ul = WebDriverWait(driver, wait_timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, list_ul_selector))
                )

                # --- XPath 생성 로직 수정 ---
                base_xpath_for_ul = ""
                if '#' in list_ul_selector:
                    # '#' 앞부분 태그와 ID, 뒷부분 선택자로 분리하여 XPath 생성 시도
                    parts = list_ul_selector.split('#', 1)
                    # 태그 없으면 *
                    tag_before_id = parts[0] if parts[0] else '*' 
                    id_and_rest = parts[1].split(' ', 1)
                    element_id = id_and_rest[0]
                    rest_selector = id_and_rest[1] if len(id_and_rest) > 1 else ''

                    # XPath 구성
                    base_xpath_for_ul = f"//{tag_before_id}[@id='{element_id}']"
                    if rest_selector:
                         # 간단히 공백을 //로 변환 (더 복잡한 CSS는 별도 처리 필요)
                        base_xpath_for_ul += "//" + rest_selector.strip().replace(' > ', '//').replace(' ', '//')

                else:
                    # '#'가 없는 경우: CSS 선택자를 간단한 XPath로 변환
                    base_xpath_for_ul = "//" + list_ul_selector.replace(' > ', '//').replace(' ', '//').replace('.', '[contains(@class, "') + '")]' # 클래스 변환 추가 시도

                # 최종 li XPath 생성
                li_xpath = f"({base_xpath_for_ul}/li)[{index + 1}]"
                # --------------------------

                # 현재 인덱스의 li 요소 대기 및 찾기
                li = WebDriverWait(driver, wait_timeout).until(
                    EC.visibility_of_element_located((By.XPATH, li_xpath))
                )

                # --- 클릭 전 정보 추출 ---
                    # '시도': xy_info['시도'],
                    # '자치구명': xy_info['자치구명'],
                    # '법적동명': xy_info['법적동명'],
                bang_info = {}
                details_text = None
                try:
                    # 가격/정보 담긴 div 추출
                    # 예: 클래스 이름 'content'를 가진 div를 찾는다고 가정 (실제 클래스 이름 확인 필요)
                    # content_div = li.find_element(By.CSS_SELECTOR, "div.content") # 이 부분이 중요! 실제 구조 확인
                    # 또는 기존처럼 인덱스 사용 (단, 불안정)
                    div_elements = li.find_elements(By.TAG_NAME, "div")
                    if len(div_elements) > 3: # 인덱스 3이 존재하는지 확인
                        content_div = div_elements[3]
                        details_text = content_div.text
                    else:
                        print(f"경고: 매물 {index+1}: 상세 정보 div 구조가 예상과 다릅니다.")
                        details_text = "" # 기본값 또는 오류 처리

                except NoSuchElementException:
                    print(f"경고: 매물 {index+1}: 이미지 또는 상세 정보 div를 찾을 수 없습니다.")
                except Exception as e:
                    print(f"경고: 매물 {index+1}: 정보 사전 추출 중 오류: {e}")

                # --- 상세 정보 텍스트 파싱 ---
                
                if details_text:
                    details = details_text.split('\n')
                    try:
                        if len(details) > 0:
                            price_part = details[0].split(' ')
                            bang_info["방식"] = price_part[0].strip()
                            if len(price_part) > 1:
                                if bang_info["방식"] == "월세":
                                    money_info = price_part[1].split('/')
                                    if len(money_info) == 2:
                                        bang_info["보증금"] = money_info[0]
                                        bang_info["월세"] = money_info[1]
                                elif bang_info["방식"] == "전세":
                                    bang_info["전세금"] = price_part[1]
                                else: # 매매 등
                                    bang_info["매매금"] = price_part[1]

                        if len(details) > 1:
                            bang_info["건물 형식"] = details[1].strip()

                        if len(details) > 2:
                            spec_parts = details[2].split(',')
                            if len(spec_parts) > 0:
                                bang_info["층수"] = spec_parts[0].strip()
                            if len(spec_parts) > 1:
                                area_part = spec_parts[1].split('m²')[0].strip()
                                bang_info["면적(m²)"] = area_part
                                try:
                                    bang_info["임대면적"] = round(float(area_part) / 3.3058, 2)
                                except ValueError:
                                    bang_info["임대면적"] = None
                            if len(spec_parts) > 2:
                                # '관리비 5만' -> '5만' -> '5'
                                fee_parts = spec_parts[2].strip().split(' ')
                                if len(fee_parts) > 1:
                                     bang_info["관리비"] = fee_parts[1].replace('만', '').strip()

                    except IndexError:
                        print(f"오류: 매물 {index+1}: 상세 정보 파싱 중 인덱스 오류. 내용: {details}")
                    except Exception as e:
                        print(f"오류: 매물 {index+1}: 상세 정보 파싱 중 오류: {e}")

                # --- li 클릭 시도 ---
                
                clicked = False
                
                try:
                    # 요소를 뷰포트로 스크롤
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", li)
                    time.sleep(0.5) # 스크롤 후 잠시 대기

                    # 클릭 가능한 상태가 될 때까지 기다린 후 클릭
                    clickable_li = WebDriverWait(driver, wait_timeout).until(
                        EC.element_to_be_clickable((By.XPATH, li_xpath)) # 다시 찾아서 클릭
                    )
                    clickable_li.click()
                    clicked = True
                    # print(f"매물 {index + 1}: 클릭 성공")
                    # 클릭 성공했을 때
                    bang_info["세부 URL"] = driver.current_url

                # 시간 초과, 요소 클릭 실패
                except (TimeoutException, ElementClickInterceptedException) as e:
                    print(f"경고: 매물 {index + 1}: 일반 클릭 실패 ({type(e).__name__}). JavaScript 클릭 시도...")
                    # 일반 클릭 실패 시 JavaScript 클릭 시도
                    # ???
                    try:
                        driver.execute_script("arguments[0].click();", li)
                        clicked = True
                        print(f"매물 {index + 1}: 클릭 성공 (JavaScriptClick)")
                    except Exception as js_e:
                        print(f"오류: 매물 {index + 1}: JavaScript 클릭도 실패: {js_e}")
                        # 클릭 실패 시 이 매물은 건너뛰고 다음 매물로
                        continue # 다음 루프 반복으로

                # --- 클릭 성공 후 상세 정보 로드 및 추출 ---
                if clicked:
                    try:
                        # container-room-root div가 나타날 때까지 기다림 (visibility_of 확인)
                        container_div = WebDriverWait(driver, wait_timeout).until(
                            EC.visibility_of_element_located((By.ID, "container-room-root"))
                        )
                        # print(f"매물 {index + 1}: 상세 정보 컨테이너 로드됨.") # 디버깅용
                        

                        # 상세 정보 내 '주변' 섹션 찾기 (필요한 경우)
                        section_element = WebDriverWait(container_div, wait_timeout).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "section[data-scroll-spy-element='near']"))
                        )
                        near_div_elements = section_element.find_elements(By.TAG_NAME, "div")
                        p_elements = section_element.find_elements(By.TAG_NAME, "p")
                        # p 태그가 존재하면
                        if p_elements:
                            try:
                                first_p_text = p_elements[0].text if p_elements else None
                                if first_p_text and any(char.isalpha() for char in first_p_text):
                                    if any('a' <= char.lower() <= 'z' for char in first_p_text):
                                        raise ValueError(f"주소 오류: {first_p_text}")
                                # print("지번주소:", first_p_text) # 디버깅용
                                bang_info['지번주소'] = first_p_text  # 첫 번째 p 태그의 텍스트를 저장
                                bang_info['시도'] = first_p_text.split(' ')[0]
                                bang_info['자치구명'] = first_p_text.split(' ')[1]
                                bang_info['법적동명'] = first_p_text.split(' ')[2]
                            except ValueError as ve:
                                print(f"오류: 매물 {index + 1}: {ve}")
                                continue  # 다음 루프로 전환


                    except TimeoutException:
                        print(f"오류: 매물 {index + 1}: 상세 정보 컨테이너(container-room-root)를 시간 내에 찾지 못했습니다.")
                    except Exception as detail_e:
                        print(f"오류: 매물 {index + 1}: 상세 정보 처리 중 오류: {detail_e}")

                bang_list.append(bang_info)

            except StaleElementReferenceException:
                print(f"Error : 매물 {index + 1} 처리 중 StaleElementReferenceException 발생. 다음 매물로 넘어갑니다.")
                continue # 다음 루프 반복으로
            except TimeoutException:
                print(f"Error : 매물 {index + 1} 처리 중 TimeoutException 발생 (li 요소를 찾거나 기다리는 중). 다음 매물로 넘어갑니다.")
                continue
            except Exception as loop_e:
                print(f"Error : 매물 {index + 1} 처리 중 예기치 않은 오류 발생: {loop_e}")
                import traceback
                traceback.print_exc() # 상세 오류 스택 출력
                continue # 다음 루프 반복으로

        # 모든 매물 처리 후 결과 반환
        if not bang_list:
             return {"errorMessage": "매물 정보를 수집하지 못했습니다."}
        return bang_list

    except TimeoutException:
        print("Error : 초기 목록 로드 실패")
        return {"errorMessage": "목록을 불러오는 데 실패했습니다."}
    except Exception as e:
        print(f"전체 프로세스 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        # 오류 객체 직접 반환 시 직렬화 문제 발생 가능성 있으므로 문자열로 변환
        return {"errorMessage": f"오류 발생: {str(e)}"}
    finally:
        if 'driver' in locals() and driver:
            driver.quit()
            print("드라이버 종료됨.")

def main():
    search_item = "동국대"
    
    # 타입 딕셔너리
    bang_dict = {
        "원룸/투룸": "onetwo",
        "아파트": "apt",
        "주택빌라": "house",
        "오피스텔": "officetel"
    }
    
    # [ "원룸/투룸", "아파트", "주택빌라", "오피스텔" ]
    rst = getDabangList(search_item, bang_type="원룸/투룸")
    
    # # *** 디버깅용 *** 
    # print("\n--- 최종 결과 ---")
    # if isinstance(rst, list):
    #     for i, item in enumerate(rst):
    #         print(f"매물 {i+1}: {item}")
    # else:
    #     print(rst)
        
    # # 결과를 DataFrame으로 변환하여 출력
    # if isinstance(rst, list) and rst:
    #     df = pd.DataFrame(rst)
    #     df.to_csv("dabang_csv_data.csv")
    # else:
    #     print("결과를 DataFrame으로 변환할 수 없습니다.")


if __name__ == "__main__":
    main()