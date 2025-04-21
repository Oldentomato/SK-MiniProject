import streamlit as st 
import folium
from streamlit_folium import st_folium
import sys, os
import requests
from geopy.geocoders import Nominatim
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import numpy as np

import pandas as pd
# 주소 정보 받아오기
from naver_api import naver_map_api as na

from module import getData
from module.format_convert import floorFormat
from module.format_convert import korean_money_to_int

geolocator = Nominatim(user_agent="streamlit_map_app")
st.set_page_config(layout="wide")


def mainView():

    st.title("부동산 매물 검색기")

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
            
            # 두 데이터프레임 합치기
            combined_df = getData.getCombinedDataFrame(address=address, option=selected_option)
            combined_df = combined_df.fillna("없음")

            st.session_state.saleList = combined_df.to_dict(orient="records")

            st.session_state.saveAddress = address #저장할 검색어 갱신
            st.session_state.searchTrigger = False #트리거 종료

            st.subheader("통합 매물 리스트")
            st.dataframe(combined_df)
        

    if st.session_state.saleList:
        col1, col2 = st.columns([2, 4])

        with col1:
            st.subheader("장소 리스트")
            selected = st.radio(
                "항목을 선택하세요",
                st.session_state.saleList,
                format_func=lambda x: x["지번주소"]
            )
            # print(selected)
            # print({
            #         "J": selected.get("자치구명"),
            #         "B": selected.get("법적동명"),
            #         "Floor": floorFormat(selected.get("층수")),
            #         "Area": selected.get("면적(m²)"),
            #         "securityMoney": korean_money_to_int(selected.get("보증금"))
            #     })
            
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
            st.markdown("---")
            
            st.subheader("상세 정보")
            st.markdown(f"예상 월 임대료:{result}만원" if result !="예측불가" else result)
            st.write(st.session_state.selected_place)
            st.write(f"층수: {selected.get('층수')}")
            st.write(f"면적: {selected.get('면적(m²)')}")
            # st.write(selected_detail)

            #지명 선택 시 지도에 마커 표시
            with st.spinner("지도 정보를 불러오는 중입니다..."):
                location = geolocator.geocode(st.session_state.selected_place)

                if location:
                    print(st.session_state.selected_place)
                    m = folium.Map(location=[location.latitude, location.longitude], zoom_start=14)
                    folium.Marker(
                        location=[location.latitude, location.longitude],
                        popup=st.session_state.selected_place,
                        icon=folium.Icon(color='blue',icon='star')
                    ).add_to(m)
                    st_folium(m, width=700, height=500)


        


if __name__ == "__main__":
    mainView()