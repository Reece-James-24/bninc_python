import streamlit as st

st.title("📄 PDF 한눈에")
st.write("PDF 문서를 업로드하고 요약/분석합니다.")

st.markdown("---")

# 예시 코드
uploaded_file = st.file_uploader(
    "PDF 파일을 업로드하세요",
    type=["pdf"]
)

if uploaded_file:
    st.success("PDF 파일이 업로드되었습니다.")
    st.write(f"파일명: {uploaded_file.name}")