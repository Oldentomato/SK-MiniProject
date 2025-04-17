import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from ml_python.train import TrainModel

from zigbang import ZigbangAPI, ZigbangDataProcessor

sample_data = [
    {"name": "장소 1", "lat": 37.5665, "lon": 126.9780, "detail": "장소 1의 상세 설명입니다."},
    {"name": "장소 2", "lat": 37.5651, "lon": 126.9895, "detail": "장소 2의 상세 설명입니다."},
    {"name": "장소 3", "lat": 37.5700, "lon": 126.9825, "detail": "장소 3의 상세 설명입니다."}
]

st.session_state.select_list = sample_data

def getSaleList(lat: int, lon: int):
    all_dfs = []

    # 직방
    zigbang_types = [ 'villa', 'oneroom', 'officetel' ]

    for room in zigbang_types:
        print(f"\n매물 유형: {room}")
        api = ZigbangAPI(lat, lon, room_type=room, delta=0.003)
        try:
            item_ids = api.get_item_ids()
            # print(f"{room} 필터링된 매물 개수: {len(item_ids)}")
            details = api.get_item_details_v3(item_ids)
            df = ZigbangDataProcessor.to_dataframe(details)
            if not df.empty:
                df["출처"] = "직방"
                all_dfs.append(df)
        except Exception as e:
            print(f"직방 {room} 오류 발생: {e}")

    # 다방

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

def mainView():
    st.title("**부동산 매물 검색기**")

    if "search_clicked" not in st.session_state:
        st.session_state.search_clicked = False
    if "selected_place" not in st.session_state:
        st.session_state.selected_place = None

    address = st.text_input("주소를 입력하세요:")

    if st.button("검색"):
        st.session_state.search_clicked = True
        st.session_state.selected_place = None  # 검색하면 선택 초기화

    if st.session_state.search_clicked:
        ######################################
        # 주소 입력 시 위,경도 추출 함수 작성
        # with st.spinner("상세 정보를 불러오는 중입니다..."):
        #     ex) lat, lon = getCoordinate(address)
        ######################################
        
        #debug
        lat, lon = 37.5665, 126.9780

        # 위,경도 얻을 시, 크롤링으로 부동산 매물 리스트 받아오는 함수 작성
        # with st.spinner("상세 정보를 불러오는 중입니다..."):
        #     ex) saleList = getSaleList(lat,lon)
        # sample_data를 리스트변수로 변경할것

        with st.spinner("상세 정보를 불러오는 중입니다..."):
            sale_df = getSaleList(lat, lon)

            if sale_df.empty:
                st.warning("조회된 매물이 없습니다.")
                return

            # 🔹 지도/선택용 리스트로 변환
            select_list = []
            for idx, row in sale_df.iterrows():
                select_list.append({
                    "name": f"{row.get('주소', '알수없음')} ({row.get('출처', '')}/{row.get('매물유형', '')})",
                    "lat": row.get("위도"),
                    "lon": row.get("경도"),
                    "detail": f"{row.get('층', '')}층, 면적: {row.get('임대면적', '')}㎡, 보증금: {row.get('보증금(만원)', '')}만원"
                })
            st.session_state.select_list = select_list

        col1, col2 = st.columns([2, 1])

        with col1:
            m = folium.Map(location=[lat, lon], zoom_start=14)
            for item in sample_data:
                folium.Marker(
                    location=[item["lat"], item["lon"]],
                    popup=item["name"],
                    icon=folium.Icon(color='blue',icon='star')
                ).add_to(m)
            st_folium(m, width=700, height=500)

        with col2:
            st.subheader("장소 리스트")
            selected = st.radio(
                "항목을 선택하세요",
                [item["name"] for item in st.session_state.select_list]
            )
            
            ######################################
            # 장소 선택 시, 자치구,법정동,층,임대면적.보증금 정보가져오는 함수 작성
            #     ex) saleInfo = getSaleInfo(name)
            ######################################
            st.session_state.selected_place = selected #화면 나오기 전에 미리 데이터를 가져오고 state를 변경

        if "inference_cache" not in st.session_state: #folium 등으로 이벤트발생시 모델중복실행을 방지하기위해 캐시저장 dict선언
            st.session_state.inference_cache = {}

        if selected not in st.session_state.inference_cache: #radio변경때만 model실행
            with st.spinner("상세 정보를 불러오는 중입니다..."):
                result = TrainModel.inferenceModel("./ml_python/model/xbg_model.pkl",{
                    "자치구명": "영등포구",
                    "법정동명": "신도림동",
                    "층": 7,
                    "임대면적": 27.01,
                    "보증금(만원)": 1000
                })
                st.session_state.inference_cache[selected] = result
                
        else:
            result = st.session_state.inference_cache[selected]

        selected = st.session_state.selected_place

        
        selected_detail = next(
            (item["detail"] for item in sample_data if item["name"] == st.session_state.selected_place), ""
        )
        st.markdown("---")
        st.markdown(f"예상 월 임대료:{result}만원 오차금액 +-20만원")
        st.subheader("상세 정보")
        st.write(selected_detail)

        st.markdown("---")
        st.subheader("**전체 매물 리스트 (직방/다방 포함)**")
        st.dataframe(sale_df, use_container_width=True)




if __name__ == "__main__":
    mainView()
