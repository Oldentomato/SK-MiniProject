import requests
import time
import pandas as pd
from typing import List, Dict
from pygeohash import encode as geohash_encode  # pip install pygeohash

class ZigbangAPI:
    BASE_LIST_URL = "https://apis.zigbang.com/v2/items/{roomtype}"
    BASE_DETAIL_URL_V3 = "https://apis.zigbang.com/v3/items/{item_id}"

    def __init__(self, lat_center: float, lng_center: float, room_type: str, delta: float = 0.003):
        self.lat_center = lat_center
        self.lng_center = lng_center
        self.delta = delta
        self.lat_south = lat_center - delta
        self.lat_north = lat_center + delta
        self.lng_west = lng_center - delta
        self.lng_east = lng_center + delta
        self.room_type = room_type

    def _calculate_geohash(self) -> str:
        # 중심 좌표로 geohash 생성 (정확도: 5)
        return geohash_encode(self.lat_center, self.lng_center, precision=5)

    def _is_within_bounds(self, lat: float, lng: float) -> bool:
        # 위경도가 None이면 False 반환, 아니면 설정 범위 내인지 확인
        if lat is None or lng is None:
            return False
        return self.lat_south <= lat <= self.lat_north and self.lng_west <= lng <= self.lng_east

    def get_item_ids(self) -> List[int]:
        # geohash와 좌표 범위로 매물 ID 목록 요청 후 위경도 필터링
        geohash = self._calculate_geohash()
        url = self.BASE_LIST_URL.format(roomtype=self.room_type)
        params = {
            "geohash": geohash,
            "latSouth": self.lat_south,
            "latNorth": self.lat_north,
            "lngWest": self.lng_west,
            "lngEast": self.lng_east,
            "domain": "zigbang",
            "checkAnyItemWithoutFilter": True
        }
        response = requests.get(url, params=params)
        # print(f"[{self.room_type}] 매물 ID 요청 URL:", response.url)
        response.raise_for_status()
        items = response.json().get("items", [])

        # 위경도 필터링 적용
        return [item["itemId"] for item in items if self._is_within_bounds(item.get("lat"), item.get("lng"))]

    def get_item_details_v3(self, item_ids: List[int]) -> List[Dict]:
        details = []
        for item_id in item_ids:
            url = self.BASE_DETAIL_URL_V3.format(item_id=item_id)
            params = {"version": "", "domain": "zigbang"}
            try:
                response = requests.get(url, params=params)
                print(f"[{self.room_type}] 개별 매물 상세 요청 URL: {response.url}")
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"매물 ID {item_id} 요청 실패: {e}")
                continue

            result = response.json()
            item = result.get("item", {})

            if item:
                item_id = item.get("itemId")
                price = item.get("price", {})
                area = item.get("area", {})
                floor_info = item.get("floor", {})
                manage_cost = item.get("manageCost", {})
                address_origin = item.get("addressOrigin", {})

                detail = {
                    "매물ID": item_id,
                    "사이트": "직방",

                    "시도": address_origin.get("local1"), # 행정구역
                    "자치구명": address_origin.get("local2"),
                    "법적동명": address_origin.get("local3"),
                    "지번주소": item.get("jibunAddress"),

                    # 이미지 대체 (매물 상세 정보)
                    "세부 URL": f"https://www.zigbang.com/home/{self.room_type}/items/{item_id}",
                    
                    "방식": item.get("salesType"),          
                    "방_종류": item.get("roomType"), # ex. 원룸, 투룸
                    "건물 형식": item.get("serviceType"), # ex. 빌라

                    "보증금": price.get("deposit"),
                    "월세": price.get("rent"),
                    "관리비": manage_cost.get("amount"),
                    "관리비 포함": ', '.join(manage_cost.get("includes", [])),
                    "관리비 별도": ', '.join(manage_cost.get("notIncludes", [])),

                    "면적(m²)": area.get("전용면적M2"),
                    # 면적(평)
                    "임대면적": round(area.get("전용면적M2", 0) / 3.3058, 2),
                    
                    "층수": floor_info.get('floor'),
                    "전체 층수": floor_info.get('allFloors')
                }
                details.append(detail)

            time.sleep(0.2)  # 서버 과부하 방지용 대기
        return details

class ZigbangDataProcessor:
    @staticmethod
    def to_dataframe(items: List[Dict]) -> pd.DataFrame:
        # 결과를 pandas DataFrame으로 변환
        return pd.DataFrame(items)

if __name__ == "__main__":
    lat_center = 37.526741
    lng_center = 126.927195

    room_types = [ 'villa', 'oneroom', 'officetel' ] # 'apt',
    all_df = []

    for room in room_types:
        print(f"\n매물 유형: {room}")
        api = ZigbangAPI(lat_center, lng_center, room_type=room, delta=0.003)
        try:
            item_ids = api.get_item_ids()
            print(f"{room} 필터링된 매물 개수: {len(item_ids)}")
            details = api.get_item_details_v3(item_ids)
            df = ZigbangDataProcessor.to_dataframe(details)
            all_df.append(df)
        except Exception as e:
            print(f"{room} 오류 발생: {e}")

    # csv 파일 생성 및 저장
    if all_df:
        final_df = pd.concat(all_df, ignore_index=True)
        final_df.to_csv("zigbang_selected_info.csv", index=False)
        print("\n저장 완료: zigbang_selected_info.csv")
        