import streamlit as st
import streamlit_folium as sf
import pandas as pd
import folium
from module import async_getData
from naver_api import naver_map_api as na
from module.format_convert import floorFormat
from module.format_convert import korean_money_to_int
from naver_api import road_address_convert as ra

# --- Page Configuration ---
st.set_page_config(
    page_icon="🏠",
    page_title="부동산 정보 검색",
    layout="wide"
)

DEFAULT_LAT = 37.5665
DEFAULT_LNG = 126.9780

if 'searchTerm' not in st.session_state:
    st.session_state.searchTerm = '' # 현재 검색어
if 'selectedType' not in st.session_state:
    st.session_state.selectedType = '원룸/투룸' # 기본 선택자(방 타입)
if 'lastSearchTerm' not in st.session_state:
    st.session_state.lastSearchTerm = '' # 검색된 검색어 저장
if 'lastSelectedType' not in st.session_state:
    st.session_state.lastSelectedType = '' # 검색된 선택자(방 타입) 저장

# 검색 후 검색어를 지우기 위한 깃발
st.session_state.setdefault('clear_search_on_next_run', False)

if st.session_state.clear_search_on_next_run:
    # 깃발이 세워져 있으면, 여기서 안전하게 상태를 변경
    st.session_state.searchTerm = ''
    st.searchTerm = ''
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
    if not search_term.strip():
        st.warning("검색어를 입력해주세요.")
        st.stop()
    
    # 이전 검색 결과 저장
    st.session_state.lastSelectedType = st.session_state.selectedType
    st.session_state.lastSearchTerm = st.session_state.searchTerm

    # 지도 기준 좌표 가져오기
    adr = ra.roadAddressConvertor(st.session_state.lastSearchTerm)
    if adr is None:
        st.error(f"'{st.session_state.lastSearchTerm}'✔ 근처에 매물이 없습니다. 올바른 주소를 입력했는지 확인해주세요.")
        st.stop()
    map_info = na.mapXY(input=adr)
    st.session_state.map_lat = map_info['위도']
    st.session_state.map_lng = map_info['경도']

    # --- 검색 로직 ---
    # 직방, 다방 통합 데이터프레임 가져오기
    if st.session_state.lastSearchTerm:
        with st.spinner(f"'{adr}' 근처 '{st.session_state.lastSelectedType}' 검색 중..."):
            try:
                # df_results = getData.getCombinedDataFrame(
                df_results = async_getData.getCombinedDataFrame_threaded(
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
st.header("🗺️ 지도")
map_container = st.container()

with map_container:
    # 맵 위젯을 생성하기 전에 세션 상태를 확인하여 좌표를 설정합니다.
    # 좌표가 없으면 기본값을 사용합니다.
    map_center_lat = st.session_state.get('map_lat', DEFAULT_LAT)
    map_center_lng = st.session_state.get('map_lng', DEFAULT_LNG)
    zoom_level = 16 if 'map_lat' in st.session_state else 18
    
    # 지도 기준 좌표에 빨간 점이나 마커 표시

    # Folium map
    # location = 중심 좌표, zoom_start = 줌 레벨
    m = folium.Map(location=[map_center_lat, map_center_lng], zoom_start=zoom_level)

    folium.Marker(
        location=[map_center_lat, map_center_lng],
        popup=st.session_state.lastSearchTerm, # 클릭 시 팝업
        tooltip="기준 좌표",
        icon=folium.Icon(color='red', icon='info-sign') # 아이콘 색상을 'red'로 지정
    ).add_to(m)

    # 상태에 'search_results'가 있고, 데이터프레임이 비어있지 않은 경우에만 지도에 마커를 추가합니다.
    if 'search_results' in st.session_state and isinstance(st.session_state.search_results, pd.DataFrame) and not st.session_state.search_results.empty:
        df_map = st.session_state.search_results.copy()

        # --- 지도에 마커 추가 ---
        if '지번주소' in df_map.columns:
            with st.spinner(f"지도에 표시할 매물 {len(df_map)}건의 주소를 좌표로 변환 중..."):
                # geocode 주소로 좌표 변환
                for i, row in df_map.iterrows():
                    address = row.get('지번주소')
                    lat, lng = None, None

                    if address and isinstance(address, str) and address.strip():
                        try:
                            # Naver Geocoding API 호출
                            geo_info = na.mapXY(input=address)

                            # 좌표 정보 확인
                            if geo_info and '위도' in geo_info and '경도' in geo_info:
                                lat = float(geo_info['위도'])
                                lng = float(geo_info['경도'])

                            else:
                                # API 호출 성공했지만 좌표 정보가 없는 경우
                                st.info(f"주소 '{address}'에 대한 좌표를 찾지 못했습니다.")

                        except Exception as e:
                            st.warning(f"주소 '{address}' 좌표 검색 중 오류 발생: {e}")
                            lat, lng = None, None 

                    # --- 매물 마커 생성 ---
                    # 좌표가 유요한 경우에만
                    if lat is not None and lng is not None:
                        popup_html = f"""
                        <b>{row.get('건물 형식', 'N/A')} / {row.get('방식', 'N/A')}</b> ({row.get('사이트', 'N/A')})<br>
                        <b>주소:</b> {row.get('지번주소', 'N/A')}<br>
                        """
                        # Add price to popup
                        if row.get('방식') == '전세' and pd.notna(row.get('보증금')):
                            popup_html += f"<b>가격:</b> 전세 {row['보증금']}만원<br>"
                        elif row.get('방식') == '월세':
                            price_parts = []
                            if pd.notna(row.get('보증금')):
                                price_parts.append(f"보증금: {row['보증금']}만원")
                            if pd.notna(row.get('월세')):
                                price_parts.append(f"월세: {row['월세']}")
                            if price_parts:
                                popup_html += f"<b>가격:</b> {' / '.join(price_parts)} 만원<br>"

                        popup_html += f"<b>면적:</b> {row.get('면적(m²)', 'N/A')} m²<br>"
                        popup_html += f"<b>층수:</b> {row.get('층수', 'N/A')}<br>"
                        if pd.notna(row.get('관리비')) and int(korean_money_to_int(row.get('관리비', 0))) > 0:
                            popup_html += f"<b>관리비:</b> {row['관리비']}만원<br>"
                        else:
                            popup_html += f"<b>관리비:</b> 없음<br>"

                        url = row.get('세부 URL', '')
                        if url and isinstance(url, str) and url.startswith('http'):
                            popup_html += f'<a href="{url}" target="_blank">상세 보기</a>'

                        # 툴팁
                        tooltip_text = f"{row.get('건물 형식', '')} - {row.get('방식', '')}"

                        folium.Marker(
                            location=[lat, lng],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=tooltip_text
                        ).add_to(m)
                # --- 매물 순회 끝 ---

        else:
            st.warning("검색 결과에 '지번주소' 컬럼이 없어 매물 위치를 지도에 표시할 수 없습니다.")

    sf.folium_static(m, width=None, height=500)

# --- 지도 영역 끝 ---



# --- 정렬 조건 영역 ---
st.divider()
st.header("🔍 정렬 조건")


# --- 정렬 조건 끝 ---



# --- 검색 결과 영역 ---
st.divider()
st.header("📊 검색 결과")
results_container = st.container()

with results_container:
    if 'search_results' in st.session_state and isinstance(st.session_state.search_results, pd.DataFrame):
        df_display = st.session_state.search_results

        if not df_display.empty:
            st.write(f"'{st.session_state.lastSelectedType}' 타입 / '{st.session_state.lastSearchTerm}' 검색 결과 ({len(df_display)}건)")

            # --- 카드 Grid Layout 형식 ---
            num_columns = 3
            cols = st.columns(num_columns)

            numeric_cols = ['보증금', '월세', '관리비', '면적(m²)']
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
                        if row.get('방식') == '전세' and row.get('보증금', 0) > 0:
                            price_str = f"**전세 {int(row['보증금']):,}** 만원"
                        elif row.get('방식') == '월세':
                            price_parts = []
                            if row.get('보증금', 0) > 0:
                                price_parts.append(f"보증금 {int(row['보증금']):,}만원")
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