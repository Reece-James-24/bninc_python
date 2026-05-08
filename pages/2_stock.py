import streamlit as st

st.title("📈 주식 한눈에")
st.write("주식 데이터를 수집하고 차트로 분석합니다.")

st.markdown("---")

# 예시 코드
stock_code = st.text_input(
    "종목 코드를 입력하세요",
    placeholder="예: 005930"
)

if st.button("분석하기"):
    if stock_code:
        st.success(f"{stock_code} 종목 분석을 시작합니다.")
    else:
        st.warning("종목 코드를 입력해주세요.")