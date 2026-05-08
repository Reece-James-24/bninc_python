import streamlit as st

st.title("🍜 맛집 한눈에")
st.write("지역 기반 맛집 정보를 검색하고 추천합니다.")

st.markdown("---")

# 예시 코드
location = st.text_input(
    "지역을 입력하세요",
    placeholder="예: 강남역"
)

if st.button("맛집 찾기"):
    if location:
        st.success(f"{location} 주변 맛집을 검색합니다.")
    else:
        st.warning("지역을 입력해주세요.")