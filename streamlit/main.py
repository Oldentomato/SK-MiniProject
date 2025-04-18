import streamlit as st 
import folium
from streamlit_folium import st_folium
import sys, os
import requests
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import numpy as np

import pandas as pd
# 주소 정보 받아오기
from naver_api import naver_map_api as na

from dabang_web_scrap import getDabangList
from zigbang import ZigbangAPI, ZigbangDataProcessor

# [ '사이트', '시도', '자치구명', '법적동명', '세부 URL', '방식', '건물 형식', '보증금', '월세', '관리비', '전세금', '면적', '임대면적', '층수' ]

# 층수 문자열 int로 치환
def floorFormat(s):
    result = 0
    if s == "고":
        result = 10
    elif s == "중":
        result = 5
    elif s == "저":
        result = 3 
    else:
        if "층" in s:
            return int(s.replace("층", ""))
        result = int(s)

    return result 

# 한글 금액에서 숫자로 치환하는 함수
def korean_money_to_int(s):
    if s == np.nan:
        raise Exception("금액 누락")
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

# 직방 df 받아오기
def getSaleList(lat: float, lon: float):
    all_dfs = []
    zigbang_types = ['villa', 'oneroom', 'officetel']

    for room in zigbang_types:
        api = ZigbangAPI(lat, lon, room_type=room, delta=0.005)
        item_ids = api.get_item_ids()
        details = api.get_item_details_v3(item_ids)
        # 보증금 값 통일
        for detail in details:
            if int(detail["보증금"]) >= 10000:
                eok = detail["보증금"] // 10000
                man = detail["보증금"] % 10000
                if man == 0:
                    result = f"{eok}억"
                else:
                    result = f"{eok}억{man}"
                detail["보증금"] = result
        # details를 DataFrame으로 변환 후 all_dfs에 추가
        df = pd.DataFrame(details)
        all_dfs.append(df)

    return all_dfs
            

def getDabangDataFrame(address, bang_type):
    # bang_type_list = ["원룸/투룸", "아파트", "주택빌라", "오피스텔"]
    dabang_list = []

    try:
        bang_list = getDabangList(address, bang_type)
        if isinstance(bang_list, dict) and "errorMessage" in bang_list:
            print(f"오류 발생: {bang_list['errorMessage']}")
        elif bang_list:
            dabang_list.extend(bang_list)
    except Exception as e:
        print(f"다방 {bang_type} 오류 발생: {e}")

    return dabang_list
    


def mainView():

    st.title("부동산 매물 검색기")

        #centroid
    lat, lon = 37.5665, 126.9780


    if "selected_place" not in st.session_state:
        st.session_state.selected_place = None

    if "searchTrigger" not in st.session_state:
        st.session_state.searchTrigger = False

    if "saveAddress" not in st.session_state:
        st.session_state.saveAddress = None

    if "saleList" not in st.session_state:
        st.session_state.saleList = []

    if "selectedType" not in st.session_state:
        st.session_state.selectedType = None


    address = st.text_input("주소를 입력하세요:")

    options = ["원룸/투룸", "아파트", "주택빌라", "오피스텔"]

    # 드롭다운 만들기
    selected_option = st.selectbox('방 종류를 선택하세요:', options)

    if st.button("검색"):
        st.session_state.selected_place = None  # 검색하면 선택 초기화
        st.session_state.searchTrigger = True if address != st.session_state.saveAddress or selected_option != st.session_state.selectedType else False #버튼을 클릭하는 순간에 저장된 검색어와 현재 검색어를 비교하고 다르면 트리거발생시킴

    if st.session_state.searchTrigger:
        with st.spinner("상세 정보를 불러오는 중입니다..."):
            # 좌표 데이터
            xy_data = na.mapXY(address)
            
            zigbang_list = getSaleList(float(xy_data["위도"]), float(xy_data["경도"]))
            dabang_list = getDabangDataFrame(address, selected_option)

            # 직방 리스트를 DataFrame으로 변환
            zigbang_df = pd.concat(zigbang_list, ignore_index=True) if zigbang_list else pd.DataFrame()

            # 다방 리스트를 DataFrame으로 변환
            dabang_df = pd.DataFrame(dabang_list) if dabang_list else pd.DataFrame()
            if not dabang_df.empty:
                dabang_df.insert(0, "사이트", "다방")

            # 두 데이터프레임 합치기
            combined_df = pd.concat([zigbang_df, dabang_df], ignore_index=True)

            st.session_state.saleList = combined_df.to_dict(orient="records")

            st.session_state.saveAddress = address #저장할 검색어 갱신
            st.session_state.searchTrigger = False #트리거 종료

            st.subheader("통합 매물 리스트")
            st.dataframe(combined_df)
        

    if st.session_state.saleList:
        col1, col2 = st.columns([2, 1])

        # with col1:
        #     m = folium.Map(location=[lat, lon], zoom_start=14)
        #     for item in xy_data:
        #         folium.Marker(
        #             location=[item["위도"], item["경도"]],
        #             popup=item["name"],
        #             icon=folium.Icon(color='blue',icon='star')
        #         ).add_to(m)
        #     st_folium(m, width=700, height=500)

        with col1:
            st.subheader("장소 리스트")
            selected = st.radio(
                "항목을 선택하세요",
                st.session_state.saleList,
                format_func=lambda x: x["지번주소"]
            )
            print(selected)
            print({
                    "J": selected.get("자치구명"),
                    "B": selected.get("법적동명"),
                    "Floor": floorFormat(selected.get("층수")),
                    "Area": selected.get("면적(m²)"),
                    "securityMoney": korean_money_to_int(selected.get("보증금"))
                })
            
            st.session_state.selected_place = selected.get("지번주소") #화면 나오기 전에 미리 데이터를 가져오고 state를 변경

        if "inference_cache" not in st.session_state: #folium 등으로 이벤트발생시 모델중복실행을 방지하기위해 캐시저장 dict선언
            st.session_state.inference_cache = {}

        if st.session_state.selected_place not in st.session_state.inference_cache: #radio변경때만 model실행
            with st.spinner("상세 정보를 불러오는 중입니다..."):
                try:
                    res = requests.post("http://devtomato.synology.me:9904/api/model/getModelResult", json={
                        "J": selected.get("자치구명"),
                        "B": selected.get("법적동명"),
                        "Floor": floorFormat(selected.get("층수")),
                        "Area": selected.get("면적(m²)"),
                        "securityMoney": korean_money_to_int(selected.get("보증금"))
                    })

                    if res.ok:
                        result = res.json()["content"]
                        st.session_state.inference_cache[st.session_state.selected_place] = result
                except Exception as e:
                    print(f"Error: {e}")
                    result = "예측불가"
                
        else:
            result = st.session_state.inference_cache[st.session_state.selected_place]


        with col2:
            # selected_detail = next(
            #     (item["detail"] for item in sample_data if item["name"] == st.session_state.selected_place), ""
            # )
            st.markdown("---")
            st.markdown(f"예상 월 임대료:{result}만원" if result !="예측불가" else result)
            st.subheader("상세 정보")
            st.write(st.session_state.selected_place)
            # st.write(selected_detail)


if __name__ == "__main__":
    mainView()