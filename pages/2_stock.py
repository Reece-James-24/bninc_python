import os
import xml.etree.ElementTree as ET
from urllib.parse import quote

import FinanceDataReader as fdr
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

st.title("📈 주식 한눈에")
st.markdown("오늘 눈여겨볼 종목과 관련 뉴스, AI 질문 답변을 간편히 확인할 수 있습니다.")
with st.container(border=True):
    st.markdown("#### 사용 방법")
    st.markdown("""
    1. **오늘의 관심 종목**에서 주목할 만한 종목을 확인합니다.
    2. **뉴스 보기**에서 종목 관련 기사와 뉴스 분위기를 확인합니다.
    3. **질문하기**에서 종목에 대해 궁금한 점을 AI에게 물어봅니다.
    """)
st.info("💡 이 페이지는 투자 참고용 정보 제공 서비스이며, 매수/매도 추천이 아닙니다.")

st.markdown("---")

POPULAR_DOMESTIC_CODES = [
    "005930.KS", "000660.KS", "035420.KS", "035720.KS",
    "005380.KS", "000270.KS", "373220.KS", "207940.KS",
    "068270.KS", "005490.KS"
]

POPULAR_OVERSEAS_CODES = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN",
    "GOOGL", "META", "NFLX", "AMD", "AVGO"
]


@st.cache_data(ttl=86400)
def load_stock_list(market_type):
    if market_type == "국내 주식":
        df = fdr.StockListing("KRX")
        df = df[["Name", "Code"]].dropna()
        df["Code"] = df["Code"].astype(str).str.zfill(6)
        df["yf_code"] = df["Code"] + ".KS"
        df["display"] = df["Name"] + " (" + df["Code"] + ")"
        df["keyword"] = df["Name"]
        return df

    nasdaq = fdr.StockListing("NASDAQ")
    nyse = fdr.StockListing("NYSE")
    df = pd.concat([nasdaq, nyse], ignore_index=True)
    df = df[["Name", "Symbol"]].dropna()
    df = df.drop_duplicates(subset=["Symbol"])
    df["yf_code"] = df["Symbol"]
    df["display"] = df["Name"] + " (" + df["Symbol"] + ")"
    df["keyword"] = df["Name"]
    return df


@st.cache_data(ttl=300)
def load_stock_data(code, period="6mo"):
    df = yf.download(code, period=period, auto_adjust=True, progress=False)

    if df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA60"] = df["Close"].rolling(60).mean()
    df["Daily_Return"] = df["Close"].pct_change()

    return df


def safe_pct(current, past):
    if past == 0:
        return 0
    return ((current - past) / past) * 100


def find_stock_info_by_code(code, market_type):
    stock_df = load_stock_list(market_type)
    found = stock_df[stock_df["yf_code"] == code]

    if found.empty:
        return {"name": code, "code": code, "keyword": code}

    row = found.iloc[0]
    return {
        "name": row["Name"],
        "code": row["yf_code"],
        "keyword": row["keyword"]
    }


def analyze_stock(df):
    latest_close = float(df["Close"].iloc[-1])
    prev_close = float(df["Close"].iloc[-2])
    five_day_past = float(df["Close"].iloc[-5])
    twenty_day_past = float(df["Close"].iloc[-20])

    change_rate = safe_pct(latest_close, prev_close)
    five_day_return = safe_pct(latest_close, five_day_past)
    twenty_day_return = safe_pct(latest_close, twenty_day_past)
    volatility = float(df["Daily_Return"].tail(20).std() * 100)

    latest_ma5 = float(df["MA5"].iloc[-1])
    latest_ma20 = float(df["MA20"].iloc[-1])
    latest_ma60 = float(df["MA60"].iloc[-1]) if not pd.isna(df["MA60"].iloc[-1]) else latest_ma20

    recent_volume = float(df["Volume"].tail(5).mean())
    past_volume = float(df["Volume"].tail(20).mean())
    volume_change = safe_pct(recent_volume, past_volume)

    recent_high = float(df["Close"].tail(60).max())
    high_gap = safe_pct(latest_close, recent_high)

    score = 50
    score_detail = {}

    if five_day_return >= 5:
        score += 16
        score_detail["최근 5일 흐름"] = "+16점"
    elif five_day_return >= 2:
        score += 10
        score_detail["최근 5일 흐름"] = "+10점"
    elif five_day_return >= 0:
        score += 5
        score_detail["최근 5일 흐름"] = "+5점"
    elif five_day_return <= -5:
        score -= 14
        score_detail["최근 5일 흐름"] = "-14점"
    else:
        score -= 6
        score_detail["최근 5일 흐름"] = "-6점"

    if twenty_day_return >= 8:
        score += 14
        score_detail["최근 20일 흐름"] = "+14점"
    elif twenty_day_return >= 3:
        score += 9
        score_detail["최근 20일 흐름"] = "+9점"
    elif twenty_day_return >= 0:
        score += 4
        score_detail["최근 20일 흐름"] = "+4점"
    elif twenty_day_return <= -8:
        score -= 12
        score_detail["최근 20일 흐름"] = "-12점"
    else:
        score -= 5
        score_detail["최근 20일 흐름"] = "-5점"

    if latest_ma5 > latest_ma20 > latest_ma60:
        score += 18
        ma_signal = "강한 상승 흐름"
        score_detail["평균선 흐름"] = "+18점"
    elif latest_ma5 > latest_ma20:
        score += 12
        ma_signal = "상승 흐름"
        score_detail["평균선 흐름"] = "+12점"
    elif latest_ma5 < latest_ma20:
        score -= 10
        ma_signal = "주의 흐름"
        score_detail["평균선 흐름"] = "-10점"
    else:
        ma_signal = "보통"
        score_detail["평균선 흐름"] = "0점"

    if volume_change >= 50:
        score += 14
        volume_signal = "거래량 크게 증가"
        score_detail["거래량"] = "+14점"
    elif volume_change >= 20:
        score += 9
        volume_signal = "거래량 증가"
        score_detail["거래량"] = "+9점"
    elif volume_change >= 0:
        score += 3
        volume_signal = "거래량 소폭 증가"
        score_detail["거래량"] = "+3점"
    else:
        score -= 3
        volume_signal = "거래량 감소"
        score_detail["거래량"] = "-3점"

    if volatility >= 5:
        score -= 12
        risk_level = "높음"
        score_detail["가격 변동"] = "-12점"
    elif volatility >= 3:
        score -= 6
        risk_level = "다소 높음"
        score_detail["가격 변동"] = "-6점"
    else:
        score += 5
        risk_level = "보통"
        score_detail["가격 변동"] = "+5점"

    if high_gap >= -5:
        score += 8
        position_signal = "최근 고점 근처"
        score_detail["가격 위치"] = "+8점"
    elif high_gap <= -20:
        score -= 8
        position_signal = "최근 고점 대비 많이 내려옴"
        score_detail["가격 위치"] = "-8점"
    else:
        position_signal = "중간 구간"
        score_detail["가격 위치"] = "0점"

    return {
        "latest_close": latest_close,
        "change_rate": change_rate,
        "five_day_return": five_day_return,
        "twenty_day_return": twenty_day_return,
        "volatility": volatility,
        "volume_change": volume_change,
        "ma_signal": ma_signal,
        "volume_signal": volume_signal,
        "risk_level": risk_level,
        "position_signal": position_signal,
        "high_gap": high_gap,
        "score": score,
        "score_detail": score_detail,
    }


@st.cache_data(ttl=600)
def get_news(keyword):
    query = f"{keyword} 주식"
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=ko&gl=KR&ceid=KR:ko"

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall(".//item")[:10]

        news_list = []
        for item in items:
            title = item.findtext("title")
            link = item.findtext("link")
            if title and link:
                news_list.append({"title": title, "link": link})

        return news_list

    except Exception:
        return []


def classify_news_title(title):
    positive_words = [
        "상승", "급등", "강세", "호실적", "성장", "수혜", "기대", "확대",
        "회복", "돌파", "최대", "개선", "신고가", "흑자", "증가", "상향",
        "AI", "반도체", "수주", "계약", "투자", "실적"
    ]
    negative_words = [
        "하락", "급락", "부진", "우려", "약세", "적자", "감소", "위기",
        "리스크", "둔화", "악화", "하향", "손실", "규제", "압박",
        "소송", "감산", "침체"
    ]

    pos_hits = [word for word in positive_words if word in title]
    neg_hits = [word for word in negative_words if word in title]

    if len(pos_hits) > len(neg_hits):
        return "긍정", pos_hits
    if len(neg_hits) > len(pos_hits):
        return "부정", neg_hits
    return "중립", []


def analyze_news_sentiment(news_list):
    result = {
        "긍정": 0,
        "부정": 0,
        "중립": 0,
        "positive_keywords": [],
        "negative_keywords": [],
        "detail": []
    }

    for news in news_list:
        label, keywords = classify_news_title(news["title"])
        result[label] += 1

        if label == "긍정":
            result["positive_keywords"].extend(keywords)
        elif label == "부정":
            result["negative_keywords"].extend(keywords)

        result["detail"].append({
            "title": news["title"],
            "label": label,
            "keywords": keywords
        })

    total = len(news_list)

    if total == 0:
        return {
            "mood": "뉴스 부족",
            "positive_ratio": 0,
            "negative_ratio": 0,
            "neutral_ratio": 0,
            "news_score": 0,
            "summary": "분석할 뉴스가 부족합니다.",
            "detail": []
        }

    positive_ratio = round((result["긍정"] / total) * 100)
    negative_ratio = round((result["부정"] / total) * 100)
    neutral_ratio = round((result["중립"] / total) * 100)

    news_score = (result["긍정"] * 5) - (result["부정"] * 5)

    if result["긍정"] > result["부정"] and positive_ratio >= 40:
        mood = "긍정 뉴스가 더 많음"
    elif result["부정"] > result["긍정"] and negative_ratio >= 40:
        mood = "부정 뉴스 주의"
    else:
        mood = "중립에 가까움"

    pos_keywords = sorted(set(result["positive_keywords"]))
    neg_keywords = sorted(set(result["negative_keywords"]))

    summary = (
        f"총 {total}건 중 긍정 {result['긍정']}건, "
        f"부정 {result['부정']}건, 중립 {result['중립']}건입니다."
    )

    if pos_keywords:
        summary += f" 긍정 키워드: {', '.join(pos_keywords[:5])}."
    if neg_keywords:
        summary += f" 부정 키워드: {', '.join(neg_keywords[:5])}."

    return {
        "mood": mood,
        "positive_ratio": positive_ratio,
        "negative_ratio": negative_ratio,
        "neutral_ratio": neutral_ratio,
        "news_score": news_score,
        "summary": summary,
        "detail": result["detail"]
    }


def build_basic_reason(stock):
    reasons = []

    if stock["news_titles"]:
        reasons.append(f"최근 뉴스에서 '{stock['news_titles'][0]}' 이슈가 확인됐습니다.")

    if stock["twenty_day_return"] > 0:
        reasons.append(f"최근 20일 수익률이 {stock['twenty_day_return']}%로 중기 흐름이 플러스입니다.")

    if stock["volume_change"] > 20:
        reasons.append(f"거래량이 {stock['volume_change']}% 늘어 시장 관심이 커진 상태입니다.")

    if stock["ma_signal"] in ["상승 흐름", "강한 상승 흐름"]:
        reasons.append(f"평균선 기준으로 {stock['ma_signal']}입니다.")

    if stock["news_mood"] != "뉴스 부족":
        reasons.append(f"뉴스 분위기는 {stock['news_mood']}입니다.")

    if not reasons:
        reasons.append("주가 흐름, 거래량, 뉴스 분위기를 종합했을 때 후보군 안에서 점수가 높았습니다.")

    return reasons[:4]


def ask_llm_recommend_reason(stock):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return build_basic_reason(stock)

    client = OpenAI(api_key=api_key)

    news_titles = "\n".join([f"- {title}" for title in stock["news_titles"][:5]])

    prompt = f"""
너는 주식 정보를 초보자에게 쉽게 설명하는 도우미야.
아래 종목이 오늘의 관심 종목으로 올라온 이유를 아주 구체적으로 설명해줘.

절대 매수/매도 추천은 하지 마.
"수익률이 올랐다" 같은 뻔한 말만 하지 말고,
뉴스 제목에서 드러나는 사업/이슈/업황을 근거로 설명해.

[종목]
{stock["name"]} ({stock["code"]})

[데이터]
- 관심도 점수: {stock["score"]}점
- 최근 5일 수익률: {stock["five_day_return"]}%
- 최근 20일 수익률: {stock["twenty_day_return"]}%
- 거래량 변화: {stock["volume_change"]}%
- 변동성: {stock["volatility"]}%
- 평균선 흐름: {stock["ma_signal"]}
- 가격 위치: {stock["position_signal"]}
- 뉴스 분위기: {stock["news_mood"]}
- 긍정 뉴스 비율: {stock["positive_ratio"]}%
- 부정 뉴스 비율: {stock["negative_ratio"]}%

[최근 뉴스 제목]
{news_titles}

출력 형식:
- 3개의 bullet로 작성
- 각 bullet은 1문장
- 쉽게 설명
- "투자 판단은 본인이 신중하게 해야 합니다" 문장은 넣지 마
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 주식 데이터를 쉽게 해석하는 금융 정보 도우미다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.35
        )

        text = response.choices[0].message.content
        lines = [
            line.replace("- ", "").strip()
            for line in text.split("\n")
            if line.strip()
        ]

        return lines[:3] if lines else build_basic_reason(stock)

    except Exception:
        return build_basic_reason(stock)


def get_top_stocks(market_type):
    target_codes = POPULAR_DOMESTIC_CODES if market_type == "국내 주식" else POPULAR_OVERSEAS_CODES
    results = []

    for code in target_codes:
        df = load_stock_data(code, period="6mo")

        if df.empty or len(df) < 60:
            continue

        analysis = analyze_stock(df)
        stock_info = find_stock_info_by_code(code, market_type)

        news_list = get_news(stock_info["keyword"])
        news_analysis = analyze_news_sentiment(news_list)
        news_titles = [news["title"] for news in news_list]

        final_score = analysis["score"] + news_analysis["news_score"]
        final_score = max(0, min(100, int(final_score)))

        results.append({
            "name": stock_info["name"],
            "code": code,
            "score": final_score,
            "base_score": analysis["score"],
            "news_score": news_analysis["news_score"],
            "five_day_return": round(analysis["five_day_return"], 2),
            "twenty_day_return": round(analysis["twenty_day_return"], 2),
            "volume_change": round(analysis["volume_change"], 2),
            "volatility": round(analysis["volatility"], 2),
            "risk_level": analysis["risk_level"],
            "ma_signal": analysis["ma_signal"],
            "position_signal": analysis["position_signal"],
            "news_mood": news_analysis["mood"],
            "positive_ratio": news_analysis["positive_ratio"],
            "negative_ratio": news_analysis["negative_ratio"],
            "neutral_ratio": news_analysis["neutral_ratio"],
            "news_titles": news_titles,
        })

    if not results:
        return []

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:3]

    for stock in results:
        stock["reasons"] = ask_llm_recommend_reason(stock)

    return results


def make_easy_comment(stock_name, analysis, news_analysis):
    return (
        f"{stock_name}의 관심도 점수는 {analysis['score']}점입니다. "
        f"최근 5일 수익률은 {analysis['five_day_return']:.2f}%, "
        f"20일 수익률은 {analysis['twenty_day_return']:.2f}%입니다. "
        f"평균선 기준으로는 '{analysis['ma_signal']}', "
        f"거래량은 '{analysis['volume_signal']}' 상태입니다. "
        f"뉴스는 '{news_analysis['mood']}'으로 보입니다."
    )


def ask_llm(question, stock_name, analysis, news_list, news_analysis):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일에 API 키를 추가해주세요."

    client = OpenAI(api_key=api_key)
    news_titles = "\n".join([f"- {news['title']}" for news in news_list[:7]])

    prompt = f"""
너는 초보 투자자에게 주식 정보를 쉽게 설명하는 도우미야.
절대 매수/매도 추천을 하지 말고, 투자 판단 참고용으로만 설명해.

[종목]
{stock_name}

[주가 데이터]
- 관심도 점수: {analysis['score']}점
- 현재가: {analysis['latest_close']:.2f}
- 전일 대비: {analysis['change_rate']:.2f}%
- 최근 5일 수익률: {analysis['five_day_return']:.2f}%
- 최근 20일 수익률: {analysis['twenty_day_return']:.2f}%
- 거래량 변화: {analysis['volume_change']:.2f}%
- 변동성: {analysis['volatility']:.2f}%
- 평균선 흐름: {analysis['ma_signal']}
- 가격 변동 위험: {analysis['risk_level']}
- 최근 위치: {analysis['position_signal']}

[뉴스 분석]
- 뉴스 분위기: {news_analysis['mood']}
- 긍정 비율: {news_analysis['positive_ratio']}%
- 부정 비율: {news_analysis['negative_ratio']}%
- 중립 비율: {news_analysis['neutral_ratio']}%
- 요약: {news_analysis['summary']}

[관련 뉴스 제목]
{news_titles}

[사용자 질문]
{question}

답변 규칙:
1. 한국어로 쉽게 답해.
2. 어려운 용어는 짧게 풀어서 설명해.
3. 데이터와 뉴스를 근거로 답해.
4. 질문에 맞는 답을 해. 모든 질문에 같은 답을 하지 마.
5. 매수/매도하라고 말하지 마.
6. 마지막에 "투자 판단은 본인이 신중하게 해야 합니다."를 붙여.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "너는 주식 데이터를 쉽게 설명하는 금융 정보 도우미다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"LLM 답변 생성 중 오류가 발생했습니다: {e}"


def render_stock_selector(key_prefix):
    market_type = st.radio(
        "시장 선택",
        ["국내 주식", "해외 주식"],
        horizontal=True,
        key=f"{key_prefix}_market"
    )

    stock_df = load_stock_list(market_type)
    placeholder = "예: 삼성, 카카오, 현대" if market_type == "국내 주식" else "예: Apple, Tesla, NVIDIA"

    keyword = st.text_input(
        "종목명을 입력하세요",
        placeholder=placeholder,
        key=f"{key_prefix}_keyword"
    )

    if keyword:
        filtered_df = stock_df[
            stock_df["display"].str.contains(keyword, case=False, na=False)
        ].head(20)
    else:
        filtered_df = stock_df.head(20)

    if filtered_df.empty:
        st.warning("검색 결과가 없습니다.")
        return None

    selected_label = st.selectbox(
        "연관 종목",
        filtered_df["display"].tolist(),
        key=f"{key_prefix}_select"
    )

    selected_row = filtered_df[filtered_df["display"] == selected_label].iloc[0]

    return {
        "name": selected_row["Name"],
        "code": selected_row["yf_code"],
        "keyword": selected_row["keyword"]
    }


tab_recommend, tab_news, tab_chat = st.tabs(
    ["🔥 오늘의 관심 종목", "📰 뉴스 보기", "💬 질문하기"]
)


with tab_recommend:
    st.subheader("🔥 오늘의 관심 종목 TOP 3")
    st.markdown("""
    주가 흐름, 거래량, 뉴스 분위기를 함께 분석해 오늘 참고해볼 만한 종목을 보여줍니다.
    """)

    market = st.radio(
        "어느 시장을 볼까요?",
        ["국내 주식", "해외 주식"],
        horizontal=True,
        key="recommend_market"
    )

    if st.button("관심 종목 보기", key="recommend_button"):
        with st.spinner("주가 데이터와 뉴스를 함께 분석 중입니다..."):
            top_stocks = get_top_stocks(market)

        if top_stocks:
            for idx, stock in enumerate(top_stocks, start=1):
                with st.container(border=True):
                    st.markdown(f"### {idx}. {stock['name']}")
                    st.caption(f"종목 코드: {stock['code']}")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("최종 관심도", f"{stock['score']}점")
                    col2.metric("주가 점수", f"{stock['base_score']}점")
                    col3.metric("뉴스 점수", f"{stock['news_score']}점")

                    st.markdown("#### 핵심 지표")
                    metric_col1, metric_col2 = st.columns(2)

                    with metric_col1:
                        st.write(f"- 최근 5일 수익률: **{stock['five_day_return']}%**")
                        st.write(f"- 최근 20일 수익률: **{stock['twenty_day_return']}%**")
                        st.write(f"- 거래량 변화: **{stock['volume_change']}%**")

                    with metric_col2:
                        st.write(f"- 평균선 흐름: **{stock['ma_signal']}**")
                        st.write(f"- 뉴스 분위기: **{stock['news_mood']}**")
                        st.write(
                            f"- 뉴스 비율: 긍정 **{stock['positive_ratio']}%** / "
                            f"부정 **{stock['negative_ratio']}%** / "
                            f"중립 **{stock['neutral_ratio']}%**"
                        )

                    st.markdown("#### 이 종목이 올라온 이유")
                    for reason in stock["reasons"]:
                        st.write(f"- {reason}")

                    with st.expander("관련 뉴스 제목 보기"):
                        for title in stock["news_titles"][:5]:
                            st.write(f"- {title}")
        else:
            st.warning("관심 종목을 불러올 수 없습니다.")


with tab_news:
    st.subheader("📰 뉴스 보기")
    st.markdown("""
    종목명을 검색하면 관련 뉴스를 불러오고, 뉴스 제목을 기준으로 긍정·부정·중립 분위기를 간단히 분석합니다.
    """)

    selected_stock = render_stock_selector("news")

    if selected_stock:
        news_list = get_news(selected_stock["keyword"])
        news_analysis = analyze_news_sentiment(news_list)

        if news_list:
            st.markdown("### 관련 뉴스")

            for news in news_list:
                with st.container(border=True):
                    st.markdown(f"**{news['title']}**")
                    st.link_button("기사 보기", news["link"])

            st.markdown("### 뉴스 분위기 분석")
            st.success(f"판단 결과: {news_analysis['mood']}")

            col1, col2, col3 = st.columns(3)
            col1.metric("긍정", f"{news_analysis['positive_ratio']}%")
            col2.metric("부정", f"{news_analysis['negative_ratio']}%")
            col3.metric("중립", f"{news_analysis['neutral_ratio']}%")

            with st.container(border=True):
                st.write(news_analysis["summary"])

            with st.expander("뉴스별 판단 보기"):
                for item in news_analysis["detail"]:
                    st.write(f"- **{item['label']}** | {item['title']}")
        else:
            st.warning("관련 뉴스를 불러오지 못했습니다.")


with tab_chat:
    st.subheader("💬 질문하기")
    st.markdown("""
    관심 있는 종목을 선택하고 궁금한 점을 입력하면, AI가 주가 데이터와 관련 뉴스를 참고해 답변합니다.
    """)

    selected_stock = render_stock_selector("chat")

    if selected_stock:
        df = load_stock_data(selected_stock["code"])

        if df.empty or len(df) < 60:
            st.error("주식 데이터를 불러올 수 없습니다.")
        else:
            analysis = analyze_stock(df)
            news_list = get_news(selected_stock["keyword"])
            news_analysis = analyze_news_sentiment(news_list)

            st.markdown("### 현재 선택 종목")

            with st.container(border=True):
                st.markdown(f"#### {selected_stock['name']}")
                st.caption(f"종목 코드: {selected_stock['code']}")
                st.write(make_easy_comment(selected_stock["name"], analysis, news_analysis))

            question = st.text_area(
                "궁금한 점을 입력하세요",
                placeholder="예: 이 회사가 요즘 주목받는 이유가 뭐야?",
                key="chat_question",
                height=100
            )

            if st.button("질문하기", key="chat_button"):
                if question:
                    with st.spinner("LLM이 종목 데이터와 뉴스를 보고 답변 중입니다..."):
                        answer = ask_llm(
                            question,
                            selected_stock["name"],
                            analysis,
                            news_list,
                            news_analysis
                        )
                    st.markdown("### AI 답변")

                    with st.container(border=True):
                        st.write(answer)
                else:
                    st.warning("질문을 입력해주세요.")