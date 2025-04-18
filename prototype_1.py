import streamlit as st
import streamlit_folium as folium
import pandas as pd
from module import getData
from naver_api import naver_map_api as na

# --- Page Configuration ---
st.set_page_config(
    page_icon="🏠",
    page_title="부동산 정보 검색",
    layout="wide"
)

DEFAULT_LAT = 37.5665
DEFAULT_LNG = 126.9780

if 'searchTerm' not in st.session_state:
    st.session_state.searchTerm = '' # current text input value
if 'selectedType' not in st.session_state:
    st.session_state.selectedType = '원룸/투룸' # Default selection
if 'lastSearchTerm' not in st.session_state:
    st.session_state.lastSearchTerm = '' # Store the term that was actually searched
if 'lastSelectedType' not in st.session_state:
    st.session_state.lastSelectedType = '' # Store the type that was actually searched
st.session_state.setdefault('clear_search_on_next_run', False)

# 스크립트 상단 (위젯 생성 전)
if st.session_state.clear_search_on_next_run:
    # 깃발이 세워져 있으면, 여기서 안전하게 상태를 변경!
    st.session_state.searchTerm = ''
    search_term = st.session_state.searchTerm
    # 처리했으니 깃발을 다시 내린다 (False로 변경)
    st.session_state.clear_search_on_next_run = False


# --- Main Application UI ---

st.title("부동산 정보 🏠")
st.subheader("원하는 조건으로 쉽게 검색하세요")

# --- 검색 바 ---
with st.form("search_form"):
    search_col1, search_col2, search_col3 = st.columns([1, 3, 1])

    with search_col1:
        # 타입
        options = ["원룸/투룸", "아파트", "오피스텔"]
        try:
            default_index = options.index(st.session_state.selectedType)
        except ValueError:
            default_index = 0

        selected_type = st.selectbox(
            "매물 타입",
            options,
            index=default_index,
            key="selectedType"
        )

    with search_col2:
        search_term = st.text_input(
            "검색어 (예: 지역명, 지하철역)",
            value=st.session_state.searchTerm,
            placeholder="Search...",
            key="searchTerm" 
        )

    with search_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Search")

# --- Search Handling ---
# 이 블락은 submit button이 클릭되었을 때만 실행됨
if submitted:
    # 이전 검색 결과 저장
    st.session_state.lastSelectedType = st.session_state.selectedType
    st.session_state.lastSearchTerm = st.session_state.searchTerm

    # 지도 기준 좌표 가져오기
    map_info = na.mapXY(input=st.session_state.lastSearchTerm)
    st.session_state.map_lat = map_info['위도']
    st.session_state.map_lng = map_info['경도']

    # --- 검색 로직 ---
    # st.success(f"검색 실행: 타입='{st.session_state.lastSelectedType}', 검색어='{st.session_state.lastSearchTerm}'")
    # st.info("실제 검색 로직을 여기에 구현하세요 (API 호출 등).")
    
    # 직방, 다방 통합 데이터프레임 가져오기
    if st.session_state.lastSearchTerm:
        with st.spinner(f"'{st.session_state.lastSearchTerm}' 근처 '{st.session_state.lastSelectedType}' 검색 중..."):
            try:
                df_results = getData.getCombinedDataFrame(
                    st.session_state.lastSearchTerm,
                    st.session_state.lastSelectedType
                )
                st.session_state.search_results = df_results
                if df_results is not None and len(df_results) > 0:
                    st.success(f"검색 완료! {len(df_results)}건의 결과를 찾았습니다.")
                    # flag을 세워서 다음 번에 검색어를 지우도록 설정
                    st.session_state.clear_search_on_next_run = True
                else:
                    st.warning(f"'{st.session_state.lastSearchTerm}' 근처 매물을 찾지 못했습니다. 😢")
            except Exception as e:
                st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
                st.session_state.search_results = pd.DataFrame()
        
    else:
        st.warning("검색어를 입력해주세요.")
        st.session_state.search_results = None
    
    # -------------------------------------


# --- 지도 영역 ---
st.divider()
st.header("🗺️ 지도 영역")
map_container = st.container()
with map_container:
    st.info("지도 컴포넌트가 여기에 표시됩니다.")
    # map_data = pd.DataFrame({'lat': [37.5665], 'lon': [126.9780]}) # Seoul 시청 기준
    # st.map(map_data)


# --- 검색 결과 영역 ---
st.divider()
st.header("📊 검색 결과 영역")
results_container = st.container()

with results_container:
    # Check if search_results exist in state and are not None
    if 'search_results' in st.session_state and isinstance(st.session_state.search_results, pd.DataFrame):
        df_display = st.session_state.search_results

        if not df_display.empty:
            st.write(f"'{st.session_state.lastSelectedType}' 타입 / '{st.session_state.lastSearchTerm}' 검색 결과 ({len(df_display)}건)")

            # --- 카드 Grid Layout 형식 ---
            num_columns = 3
            cols = st.columns(num_columns)

            numeric_cols = ['보증금', '월세', '관리비', '면적(m²)', '전세금']
            for col in numeric_cols:
                if col in df_display.columns:
                    df_display[col] = pd.to_numeric(df_display[col], errors='coerce').fillna(0)

            for i, row in df_display.iterrows():
                col_index = i % num_columns
                with cols[col_index]:
                    with st.container(border=True):
                        # --- 카드 형식 ---
                        st.markdown(f"**{row.get('건물 형식', 'N/A')} / {row.get('방식', 'N/A')}** ({row.get('사이트', 'N/A')})")

                        # 가격 정보
                        price_str = "가격 정보 없음"
                        if row.get('방식') == '전세' and row.get('전세금', 0) > 0:
                            price_str = f"**전세 {int(row['전세금']):,}** 만원"
                        elif row.get('방식') == '월세':
                            price_parts = []
                            if row.get('보증금', 0) > 0:
                                price_parts.append(f"보증금 {int(row['보증금']):,}")
                            if row.get('월세', 0) > 0:
                                price_parts.append(f"월세 {int(row['월세']):,}")
                            if price_parts:
                                price_str = f"**{' / '.join(price_parts)}** 만원"
                            else:
                                price_str = "월세 정보 없음"

                        st.markdown(price_str)

                        st.write(f"📍 **주소:** {row.get('지번주소', '')}")
                        st.write(f"📏 **면적:** {row.get('면적(m²)', 'N/A')} m²")
                        st.write(f"🏢 **층수:** {row.get('층수', 'N/A')}")

                        if row.get('관리비', 0) > 0:
                            st.write(f"💰 **관리비:** {int(row['관리비'])} 만원")
                        else:
                            st.write(f"💰 **관리비:** 없음")

                        url = row.get('세부 URL', '')
                        if url and isinstance(url, str) and url.startswith('http'):
                           st.markdown(f"[🔗 상세 보기]({url})", unsafe_allow_html=True)
                        else:
                           st.write("상세 정보 링크 없음")

                        st.write("")
                        st.write("")

        elif st.session_state.lastSearchTerm:
            st.info(f"'{st.session_state.lastSearchTerm}' 근처 '{st.session_state.lastSelectedType}' 매물이 없습니다.")

        else:
             st.write("검색 조건을 입력하고 Search 버튼을 클릭하세요.")

    else:
        st.write("검색 조건을 입력하고 Search 버튼을 클릭하세요.")