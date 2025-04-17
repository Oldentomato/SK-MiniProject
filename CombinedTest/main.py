import streamlit as st
import folium
from streamlit_folium import st_folium
import sys, os
import pandas as pd
import joblib
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from ml_python.train import TrainModel
from zigbang import ZigbangAPI, ZigbangDataProcessor
from naver_api import naver_map_api as na
from dabang_web_scrap import getDabangList

def getCoordinate(address):
    try:
        result = na.mapXY(address)
        if result and "위도" in result and "경도" in result:
            st.success(f"📍 위치 확인: {result['자치구명']} {result['법정동명']}")
            return {
                "위도": float(result["위도"]),
                "경도": float(result["경도"]),
                "자치구명": result.get("자치구명", ""),
                "법정동명": result.get("법정동명", "")
            }
        else:
            st.error("❗ 주소 변환 실패: 결과가 없습니다.")
    except Exception as e:
        st.error(f"❗ 네이버 API 호출 실패: {e}")

def getSaleList(lat: float, lon: float, query_address: str):
    all_dfs = []
    zigbang_types = ['villa', 'oneroom', 'officetel']

    for room in zigbang_types:
        api = ZigbangAPI(lat, lon, room_type=room, delta=0.003)
        try:
            item_ids = api.get_item_ids()
            details = api.get_item_details_v3(item_ids)
            df = ZigbangDataProcessor.to_dataframe(details)
            if not df.empty:
                df["출처"] = "직방"
                df["매물유형"] = room
                all_dfs.append(df)
        except Exception as e:
            print(f"직방 {room} 오류 발생: {e}")

    try:
        dabang_list = getDabangList(query_address, bang_type="원룸/투룸")
        if isinstance(dabang_list, list):
            dabang_df = pd.DataFrame(dabang_list)
            if not dabang_df.empty:
                dabang_df["출처"] = "다방"
                dabang_df["매물유형"] = dabang_df.get("방_종류", "원룸")
                dabang_df["주소"] = query_address
                dabang_df.rename(columns={"보증금": "보증금(만원)", "월세": "월세(만원)"}, inplace=True)
                all_dfs.append(dabang_df)
    except Exception as e:
        print(f"다방 오류 발생: {e}")

    full_df = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()
    return full_df, all_dfs

def getSaleInfo(name):
    for item in st.session_state.select_list:
        if item["name"] == name:
            return {
                "자치구명": item.get("자치구명"),
                "법정동명": item.get("법정동명"),
                "층": int(item.get("층")),
                "임대면적": float(item.get("임대면적")),
                "보증금(만원)": int(item.get("보증금"))
            }
    return {
        "자치구명": "영등포구",
        "법정동명": "신도림동",
        "층": 7,
        "임대면적": 27.01,
        "보증금(만원)": 1000
    }

sample_data = []

st.session_state.select_list = sample_data

def mainView():
    st.title("부동산 매물 검색기")

    if "search_clicked" not in st.session_state:
        st.session_state.search_clicked = False
    if "selected_place" not in st.session_state:
        st.session_state.selected_place = None

    address = st.text_input("주소를 입력하세요:")

    if st.button("검색"):
        st.session_state.search_clicked = True
        st.session_state.selected_place = None

    if st.session_state.search_clicked:
        coord = getCoordinate(address)
        lat, lon = coord["위도"], coord["경도"]

        with st.spinner("매물 정보를 수집 중입니다..."):
            sale_df, split_dfs = getSaleList(lat, lon, address)

        if sale_df.empty:
            st.warning("조회된 매물이 없습니다.")
            return

        select_list = []
        for idx, row in sale_df.head(10).iterrows():
            name = f"{row.get('주소', '알수없음')} ({row.get('출처', '')}/{row.get('매물유형', '')})"
            select_list.append({
                "name": name,
                "lat": row.get("위도") or row.get("lat"),
                "lon": row.get("경도") or row.get("lon"),
                "detail": f"{row.get('층', '')}층 | 면적: {row.get('임대면적', '')}㎡ | 보증금: {row.get('보증금(만원)', '')}만원",
                "자치구명": row.get("자치구명", coord["자치구명"]),
                "법정동명": row.get("법정동명", coord["법정동명"]),
                "층": row.get("층", 7),
                "임대면적": row.get("임대면적", 27.01),
                "보증금": row.get("보증금(만원)", 1000)
            })

        st.session_state.select_list = select_list

        st.markdown("---")
        st.subheader("📋 통합 매물 리스트")
        st.dataframe(sale_df, use_container_width=True, height=500)

        col1, col2 = st.columns([2, 1])

        with col1:
            m = folium.Map(location=[lat, lon], zoom_start=14)
            for item in st.session_state.select_list:
                if item["lat"] and item["lon"]:
                    folium.Marker(
                        location=[item["lat"], item["lon"]],
                        popup=item["name"],
                        icon=folium.Icon(color='blue', icon='star')
                    ).add_to(m)
            st_folium(m, width=700, height=500)

        with col2:
            st.subheader("장소 리스트")
            selected = st.radio(
                "항목을 선택하세요",
                [item["name"] for item in st.session_state.select_list]
            )
            st.session_state.selected_place = selected

        if "inference_cache" not in st.session_state:
            st.session_state.inference_cache = {}

        if selected not in st.session_state.inference_cache:
            with st.spinner("상세 정보를 불러오는 중입니다..."):
                sale_info = getSaleInfo(selected)
                model_path = os.path.join("ml_python", "model", "xbg_model.pkl")
                if not os.path.exists(model_path):
                    st.error(f"❌ 예측 모델 파일을 찾을 수 없습니다: {model_path}")
                    return
                result = TrainModel.inferenceModel(model_path, sale_info)
                st.session_state.inference_cache[selected] = result
        else:
            result = st.session_state.inference_cache[selected]

        selected = st.session_state.selected_place
        selected_detail = next(
            (item["detail"] for item in st.session_state.select_list if item["name"] == selected), ""
        )

        st.markdown("---")
        st.subheader(f"📊 선택한 매물의 예상 월 임대료: **{result}만원** ±20만원")
        st.markdown(f"**상세 정보:** {selected_detail}")

if __name__ == "__main__":
    mainView()
