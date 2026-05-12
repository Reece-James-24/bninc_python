import streamlit as st

st.set_page_config(
    page_title="한눈에",
    page_icon="👀",
    layout="wide"
)


# 홈 화면 함수
def home():
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 8px;
        }
        .sub-title {
            font-size: 20px;
            color: #666;
            margin-bottom: 10px;
        }
        .hero-box {
            padding: 28px;
            border-radius: 18px;
            background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
            border: 1px solid #e5e7eb;
            margin-bottom: 28px;
        }
        .feature-card {
            padding: 24px;
            border-radius: 18px;
            border: 1px solid #e5e7eb;
            background-color: #ffffff;
            min-height: 250px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.04);
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.08);
        }
        .feature-icon {
            font-size: 36px;
            margin-bottom: 8px;
        }
        .feature-title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .feature-desc {
            font-size: 15px;
            color: #555;
            line-height: 1.6;
            min-height: 60px;
        }
        .card-button {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 16px;
            border-radius: 12px;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white !important;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .card-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(79,70,229,0.25);
            text-decoration: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="hero-box">
            <div class="main-title">👀 한눈에</div>
            <div class="sub-title">
                PDF, 주식, 맛집 정보를 핵심만 빠르게 보여주는 통합 플랫폼
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 원하는 기능을 선택해주세요")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📄</div>
                <div class="feature-title">PDF 한눈에</div>
                <div class="feature-desc">
                    PDF 문서를 업로드하면<br>
                    AI가 핵심 내용을 요약해줍니다.
                </div>
                <a href="/pdf" target="_self" class="card-button">
                    PDF 한눈에 시작하기 →
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📈</div>
                <div class="feature-title">주식 한눈에</div>
                <div class="feature-desc">
                    오늘의 관심 종목, 관련 뉴스,<br>
                    종목별 질문 답변을 확인합니다.
                </div>
                <a href="/stock" target="_self" class="card-button">
                    주식 한눈에 시작하기 →
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🍜</div>
                <div class="feature-title">맛집 한눈에</div>
                <div class="feature-desc">
                    지역 기반으로 맛집 정보를 수집하고,<br>
                    조건에 맞는 장소를 추천합니다.
                </div>
                <a href="/restaurant" target="_self" class="card-button">
                    맛집 한눈에 시작하기 →
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )


home_page = st.Page(
    home,
    title="홈",
    icon="🏠",
    default=True,
    url_path=""
)

pdf_page = st.Page(
    "pages/1_pdf.py",
    title="PDF 한눈에",
    icon="📄",
    url_path="pdf"
)

stock_page = st.Page(
    "pages/2_stock.py",
    title="주식 한눈에",
    icon="📈",
    url_path="stock"
)

restaurant_page = st.Page(
    "pages/3_restaurant.py",
    title="맛집 한눈에",
    icon="🍜",
    url_path="restaurant"
)

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

pg.run()