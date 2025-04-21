import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pandas as pd
import threading # Import threading
import time # Optional: for timing

# 주소 정보 받아오기
from naver_api import naver_map_api as na

# 직방 다방 API 가져오기
from dabang_web_scrap import getDabangList as fetch_dabang_data
from zigbang import ZigbangAPI, ZigbangDataProcessor

# ----- 직방 -----
def getZigbangDataFrameList(lat: float, lon: float) -> list[pd.DataFrame]:
    """Fetches Zigbang data for multiple room types and returns a list of DataFrames."""
    all_dfs = []
    zigbang_types = ['villa', 'oneroom', 'officetel'] # Add 'apt' if needed

    print(f"Starting Zigbang")
    start_time = time.time()

    for room in zigbang_types:
        try:
            api = ZigbangAPI(lat, lon, room_type=room, delta=0.005)
            item_ids = api.get_item_ids()
            # 매물이 없으면 다음 타입 진행
            if not item_ids:
                continue

            details = api.get_item_details_v3(item_ids)

            if details:
                for detail in details:
                    deposit = detail.get("보증금")
                    if isinstance(deposit, (int, float)) and deposit >= 10000:
                        eok = int(deposit // 10000)
                        man = int(deposit % 10000)
                        if man == 0:
                            result = f"{eok}억"
                        else:
                            result = f"{eok}억{man:,}"
                        detail["보증금"] = result
                    elif isinstance(deposit, (int, float)):
                         detail["보증금"] = f"{int(deposit):,}"
                    elif deposit is None:
                        detail["보증금"] = None

                # details를 DataFrame으로 변환 후 all_dfs에 추가
                df = ZigbangDataProcessor.to_dataframe(details)
                all_dfs.append(df)

        except Exception as e:
            print(f"직방 오류 {room}: {e}")

    end_time = time.time()
    print(f"직방 완료 : {end_time - start_time:.2f} 초 소요. 데이터프레임 길이 : {len(all_dfs)}")
    return all_dfs

# ----- 다방 가져오기 -----
def getDabangDataFrame(address, bang_type) -> list:

    start_time = time.time()
    dabang_list = []
    try:
        bang_list_result = fetch_dabang_data(address, bang_type)
        if isinstance(bang_list_result, dict) and "errorMessage" in bang_list_result:
            print(f"Dabang API Error: {bang_list_result['errorMessage']}")
        elif isinstance(bang_list_result, list) and bang_list_result:
            dabang_list.extend(bang_list_result)
            
    except Exception as e:
        print(f"다방 오류 {bang_type}: {e}")

    end_time = time.time()
    print(f"다방 완료 : {end_time - start_time:.2f} 초 소요. 데이터프레임 길이 : {len(dabang_list)}")
    return dabang_list

# ----- 쓰레드 ( 비동기 처리 ) -----
def getCombinedDataFrame_threaded(address, option="원룸/투룸"):
    print(f"\n--- 데이터 병합 시작 : {address} ({option}) ---")
    overall_start_time = time.time()

    xy_data = na.mapXY(address)
    if not xy_data or "위도" not in xy_data or "경도" not in xy_data:
        print(f"Error: '{address}' Naver map API 오류")
        return pd.DataFrame()

    lat = float(xy_data["위도"])
    lon = float(xy_data["경도"])

    results = {
        "dabang": None,
        "zigbang": None
    }

    # 다방 스레드
    def dabang_thread_worker(addr, opt, res_dict):
        res_dict["dabang"] = getDabangDataFrame(addr, opt)

    # 직방 스레드
    def zigbang_thread_worker(latitude, longitude, res_dict):
        res_dict["zigbang"] = getZigbangDataFrameList(latitude, longitude) # Returns list of DFs

    # 스레드 생성
    dabang_thread = threading.Thread(target=dabang_thread_worker, args=(address, option, results))
    zigbang_thread = threading.Thread(target=zigbang_thread_worker, args=(lat, lon, results))

    dabang_thread.start()
    zigbang_thread.start()
    
    # 스레드 종료 대기
    dabang_thread.join()
    zigbang_thread.join()

    dabang_list = results.get("dabang", [])
    zigbang_df_list = results.get("zigbang", [])

    if dabang_list and isinstance(dabang_list, list):
        dabang_df = pd.DataFrame(dabang_list)
        if not dabang_df.empty:
            dabang_df.insert(0, "사이트", "다방")
        else:
            dabang_df = pd.DataFrame()
    else:
        print("데이터프레임 비어있음")
        dabang_df = pd.DataFrame()

    if zigbang_df_list and isinstance(zigbang_df_list, list):
        valid_zigbang_dfs = [df for df in zigbang_df_list if isinstance(df, pd.DataFrame) and not df.empty]
        if valid_zigbang_dfs:
            zigbang_df = pd.concat(valid_zigbang_dfs, ignore_index=True)

            if '시도' in zigbang_df.columns and '지번주소' in zigbang_df.columns:
                zigbang_df['시도'] = zigbang_df['시도'].fillna('')
                zigbang_df['지번주소'] = zigbang_df['지번주소'].fillna('')

                zigbang_df["temp_address_full"] = zigbang_df["시도"].astype(str) + " " + zigbang_df["지번주소"].astype(str)
                zigbang_df["temp_address_full"] = zigbang_df["temp_address_full"].str.strip()
                
                zigbang_df['지번주소'] = zigbang_df['temp_address_full']
                
                zigbang_df = zigbang_df.drop(columns=['temp_address_full'])
        else:
             zigbang_df = pd.DataFrame()
    else:
        zigbang_df = pd.DataFrame()


    if not zigbang_df.empty:
        zigbang_df.reset_index(drop=True, inplace=True)
        # 디버깅용
        # print("Zigbang DF index reset.")
        # print(zigbang_df.head())

    if not dabang_df.empty:
        dabang_df.reset_index(drop=True, inplace=True)
        # 디버깅용
        # print("Dabang DF index reset.")
        # print(dabang_df.head())


    if not zigbang_df.empty or not dabang_df.empty:
        try:
            combined_df = pd.concat([zigbang_df, dabang_df], ignore_index=True, sort=False)

            if '사이트' in combined_df.columns:
                 combined_df['사이트'] = combined_df['사이트'].fillna('직방')
            else:
                 if not zigbang_df.empty and dabang_df.empty:
                       combined_df['사이트'] = '직방'


        except Exception as concat_err:
             print(f"pd.concat Error: {concat_err}")

             if not zigbang_df.empty: 
                zigbang_df.info()
             else:
                print("직방 DF 비어있음")

             if not dabang_df.empty:
                dabang_df.info()
             else: 
                print("다방 DF 비어있음")
             combined_df = pd.DataFrame()


    else:
        print("직방, 다방 DF 모두 비어있음")
        combined_df = pd.DataFrame()

    overall_end_time = time.time()
    print(f"--- 결합 완료 : {overall_end_time - overall_start_time:.2f} 초 소요 ---")
    print(f"최종 결과 길이 : {len(combined_df)}")
    
    # "보증금" 컬럼 값 통일 만원 단위로 통일 예) 1억2000 => 12000, 2000 => 2000
    if '보증금' in combined_df.columns:
        combined_df['보증금'] = combined_df['보증금'].astype(str).replace('None', '0').str.replace('억', '', regex=False).str.replace(',', '', regex=False).str.replace('만원', '', regex=False).str.replace('원', '', regex=False).str.replace(' ', '', regex=False)
        combined_df['보증금'] = combined_df['보증금'].astype(float).fillna(0).astype(int)
    
    return combined_df


def main():
    address_to_search = "동국대학교"
    dabang_option = "원룸/투룸"

    combined_dataframe = getCombinedDataFrame_threaded(address_to_search, dabang_option)

    if not combined_dataframe.empty:
        # 디버깅용
        print(combined_dataframe.head())
        combined_dataframe.to_csv("combined_data.csv", index=False, encoding='utf-8')
    else:
        print("\nNo Data or Empty DataFrame")

if __name__ == "__main__":
    main()