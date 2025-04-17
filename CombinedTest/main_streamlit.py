import os
import sys
import streamlit as st
import folium
from streamlit_folium import st_folium
import pickle
import xgboost as xgb

# 패키지 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

# 샘플 데이터
SAMPLE_DATA = [
    {"name": "장소 1", "lat": 37.5665, "lon": 126.9780, "detail": "장소 1의 상세 설명입니다."},
    {"name": "장소 2", "lat": 37.5651, "lon": 126.9895, "detail": "장소 2의 상세 설명입니다."},
    {"name": "장소 3", "lat": 37.5700, "lon": 126.9825, "detail": "장소 3의 상세 설명입니다."}
]

MODEL_PATH = "./ml_python/model/xgb_model.pkl"

# 모델 로딩 클래스
class TrainModel:
    model = None

    @classmethod
    def load_model(cls, model_path):
        if cls.model is None:
            with open(model_path, "rb") as f:
                cls.model = pickle.load(f)

    @classmethod
    def inference(cls, model_path, input_dict):
        cls.load_model(model_path)
        input_df = xgb.DMatrix([[input_dict["층"], input_dict["임대면적"], input_dict["보증금(만원)"]]])
        prediction = cls.model.predict(input_df)
        return round(prediction[0], 2)

# 기능 함수들
def init_session_state():
    st.session_state.setdefault("search_clicked", False)
    st.session_state.setdefault("selected_place", None)
    st.session_state.setdefault("select_list", SAMPLE_DATA)
    st.session_state.setdefault("inference_cache", {})

def get_coordinate_from_address(address):
    # TODO: 실제 주소 기반 위경도 변환 구현
    return 37.5665, 126.9780

def get_sale_list(lat, lon):
    # TODO: 실제 크롤링 or API로 매물 리스트 가져오기
    return SAMPLE_DATA

def get_sale_info(place_name):
    # TODO: 실제 장소 기반 상세 정보 불러오기
    return {
        "자치구명": "영등포구",
        "법정동명": "신도림동",
        "층": 7,
        "임대면적": 27.01,
        "보증금(만원)": 1000
    }

def draw_map(lat, lon, data_list):
    map_obj = folium.Map(location=[lat, lon], zoom_start=14)
    for item in data_list:
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=item["name"],
            icon=folium.Icon(color='blue', icon='star')
        ).add_to(map_obj)
    return map_obj

# Main View
def mainView():
    st.title("**부동산 매물 검색기**")
    init_session_state()

    address = st.text_input("주소를 입력하세요:")

    if st.button("검색"):
        st.session_state.search_clicked = True
        st.session_state.selected_place = None

    if st.session_state.search_clicked:
        lat, lon = get_coordinate_from_address(address)
        sale_list = get_sale_list(lat, lon)
        st.session_state.select_list = sale_list

        col1, col2 = st.columns([2, 1])
        with col1:
            map_obj = draw_map(lat, lon, sale_list)
            st_folium(map_obj, width=700, height=500)

        with col2:
            st.subheader("장소 리스트")
            selected_name = st.radio(
                "항목을 선택하세요",
                [item["name"] for item in sale_list]
            )
            st.session_state.selected_place = selected_name

        selected_place = st.session_state.selected_place
        sale_info = get_sale_info(selected_place)

        if selected_place not in st.session_state.inference_cache:
            with st.spinner("예상 임대료 계산 중..."):
                try:
                    result = TrainModel.inference(MODEL_PATH, sale_info)
                except Exception as e:
                    st.error(f"예측 중 오류 발생: {e}")
                    result = "N/A"
                st.session_state.inference_cache[selected_place] = result
        else:
            result = st.session_state.inference_cache[selected_place]

        selected_detail = next(
            (item["detail"] for item in sale_list if item["name"] == selected_place), ""
        )

        st.markdown("---")
        st.markdown(f"**예상 월 임대료:** {result}만원 (±20만원)")
        st.subheader("상세 정보")
        st.write(selected_detail)

# Entry Point
if __name__ == "__main__":
    mainView()
