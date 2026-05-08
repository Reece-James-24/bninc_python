import streamlit as st

st.set_page_config(
    page_title="한눈에",
    page_icon="👀",
    layout="wide"
)

# 홈 화면 함수
def home():
    st.title("👀 한눈에")
    st.write("""
    PDF 분석, 주식 데이터 분석, 맛집 추천 기능을 한곳에서 사용할 수 있는 통합 플랫폼입니다.
    원하는 기능을 선택해 이동하세요.
    """)

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("## 📄 PDF 한눈에")
        st.write("PDF 문서를 업로드하고 요약/분석합니다.")
        st.page_link("pages/1_pdf.py", label="이동하기", icon="📄")

    with col2:
        st.markdown("## 📈 주식 한눈에")
        st.write("주식 데이터를 수집하고 분석합니다.")
        st.page_link("pages/2_stock.py", label="이동하기", icon="📈")

    with col3:
        st.markdown("## 🍜 맛집 한눈에")
        st.write("지역 기반 맛집 정보를 추천합니다.")
        st.page_link("pages/3_restaurant.py", label="이동하기", icon="🍜")

# 페이지 정의
home_page = st.Page(
    home,
    title="홈",
    icon="🏠",
    default=True
)
pdf_page = st.Page(
    "pages/1_pdf.py",
    title="PDF 한눈에",
    icon="📄"
)
stock_page = st.Page(
    "pages/2_stock.py",
    title="주식 한눈에",
    icon="📈"
)
restaurant_page = st.Page(
    "pages/3_restaurant.py",
    title="맛집 한눈에",
    icon="🍜"
)

# Navigation 생성
pg = st.navigation(
    {
        "서비스": [
            home_page,
            pdf_page,
            stock_page,
            restaurant_page
        ]
    }
)

# 현재 선택된 페이지 실행
pg.run()