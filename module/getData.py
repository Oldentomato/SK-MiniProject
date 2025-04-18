import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pandas as pd
# 주소 정보 받아오기
from naver_api import naver_map_api as na

from dabang_web_scrap import getDabangList
from zigbang import ZigbangAPI


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
            
# 다방 데이터 가져오기
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

# 직방 + 다방
def getCombinedDataFrame(address, option):
    # 좌표 데이터
    xy_data = na.mapXY(address)
    
    zigbang_list = getSaleList(float(xy_data["위도"]), float(xy_data["경도"]))
    dabang_list = getDabangDataFrame(address, option)

    # 직방 리스트를 DataFrame으로 변환
    zigbang_df = pd.concat(zigbang_list, ignore_index=True) if zigbang_list else pd.DataFrame()
    if not zigbang_df.empty:
        zigbang_df["지번주소"] = zigbang_df["시도"] + " " + zigbang_df["지번주소"]

    # 다방 리스트를 DataFrame으로 변환
    dabang_df = pd.DataFrame(dabang_list) if dabang_list else pd.DataFrame()
    if not dabang_df.empty:
        dabang_df.insert(0, "사이트", "다방")

    # 두 데이터프레임 합치기
    combined_df = pd.concat([zigbang_df, dabang_df], ignore_index=True)
    return combined_df


def main():
    df = getCombinedDataFrame("동국대", "원룸/투룸")
    print(df.keys())

if __name__ == "__main__":
    main()