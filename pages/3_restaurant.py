import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RestaurantService:
    def __init__(self):
        self.api_key = os.getenv("KAKAO_REST_API_KEY")
        self.url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    def get_nearby_restaurants(self, keyword, x, y, radius=1000):
        if not self.api_key:
            return "API_KEY_ERROR"
            
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        params = {
            "query": keyword,
            "x": x,
            "y": y,
            "radius": radius,
            "category_group_code": "FD6", # 음식점
            "sort": "distance"
        }
        
        try:
            response = requests.get(self.url, headers=headers, params=params)
            return response.json().get('documents', [])
        except Exception as e:
            return []            

import streamlit as st
import random
import pandas as pd

# 페이지 제목
st.title("🍜 맛집 한눈에")
st.write("카카오맵 데이터를 기반으로 현재 위치 주변의 맛집을 추천합니다.")

# 세션 상태 초기화 (추천 결과 유지용)
if 'restaurant_results' not in st.session_state:
    st.session_state.restaurant_results = []

# 사이드바 설정
with st.sidebar:
    st.header("📍 위치 및 검색 설정")
    # 기본값: 서울역 인근
    lat = st.number_input("위도(Latitude)", value=37.53051, format="%.6f")
    lon = st.number_input("경도(Longitude)", value=126.8986, format="%.6f")
    radius = st.slider("검색 반경(m)", 500, 3000, 1000, step=500)
    keyword = st.selectbox("메뉴 카테고리", ["맛집", "한식", "중식", "일식", "양식", "고기", "카페"])

# 맛집 검색 버튼
if st.sidebar.button("주변 맛집 검색", use_container_width=True):
    service = RestaurantService()
    with st.spinner("데이터를 불러오는 중..."):
        results = service.get_nearby_restaurants(keyword, str(lon), str(lat), radius)
        
        if results == "API_KEY_ERROR":
            st.error(".env 파일에 KAKAO_REST_API_KEY를 설정해주세요.")
        elif results:
            st.session_state.restaurant_results = results
        else:
            st.warning("검색 결과가 없습니다. 위치나 반경을 조절해보세요.")

# 결과 출력 영역
if st.session_state.restaurant_results:
    results = st.session_state.restaurant_results
    
    # 1. 랜덤 추천 섹션
    st.markdown("---")
    pick = random.choice(results)
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("🎲 오늘 점심은?")
    with col2:
        st.success(f"**{pick['place_name']}** ({pick['category_name'].split(' > ')[-1]})")
    
    # 2. 지도 표시
    df = pd.DataFrame([
        {'lat': float(p['y']), 'lon': float(p['x']), 'name': p['place_name']} 
        for p in results
    ])
    st.map(df)

    # 3. 리스트 상세 정보
    st.subheader(f"🔍 주변 {keyword} 리스트 (가까운 순)")
    for place in results:
        with st.expander(f"{place['place_name']} ({place['distance']}m)"):
            st.write(f"🏠 주소: {place['road_address_name'] or place['address_name']}")
            if place['phone']:
                st.write(f"📞 전화: {place['phone']}")
            st.markdown(f"[🔗 카카오맵으로 자세히 보기]({place['place_url']})")
