import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

st.title("📄 PDF 한눈에")
st.markdown("PDF 문서를 업로드하면 AI가 핵심 내용을 빠르게 요약해줍니다.")
with st.container(border=True):
    st.markdown("#### 사용 방법")
    st.markdown("""
    1. **PDF 파일을 업로드**합니다.
    2. AI가 문서 내용을 분석합니다.
    3. **요약 결과**를 확인합니다.
    """)
st.info("💡 문서 길이에 따라 분석 시간이 조금 걸릴 수 있습니다.")

st.markdown("---")

# 1. 파일 업로드
st.markdown("### 📎 파일 업로드")

with st.container(border=True):
    uploaded_file = st.file_uploader(
        "PDF 파일을 선택하세요",
        type="pdf"
    )

if uploaded_file is not None:
    # 임시 파일로 저장 (PyPDFLoader는 파일 경로가 필요함)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        with st.spinner("문서를 분석 중입니다... 잠시만 기다려주세요."):
            # 문서 로드 및 분할
            loader = PyPDFLoader(tmp_file_path)
            docs = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            splits = text_splitter.split_documents(docs)

            # 벡터 스토어 생성 (속도를 위해 인메모리 사용 권장)
            vectorstore = Chroma.from_documents(
                documents=splits, 
                embedding=OpenAIEmbeddings()
            )
            retriever = vectorstore.as_retriever()

            # RAG 체인 설정
            llm = ChatOpenAI(model="gpt-4o-mini")
            prompt = ChatPromptTemplate.from_template("""
            주어진 문맥(Context)을 바탕으로 질문에 답하세요.
            답을 모르면 모른다고 솔직하게 말하세요. 한국어로 답변하세요.

            Context: {context}
            Question: {input}
            """)

            combine_docs_chain = create_stuff_documents_chain(llm, prompt)
            rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

            response = rag_chain.invoke({"input": "이 문서의 핵심 내용을 1000자 내외로 요약해줘."})

            # 2. 요약 결과 보여주기
            st.success("✅ 분석이 완료되었습니다.")
            st.markdown("### 📝 문서 요약 결과")

            with st.container(border=True):
                st.write(response["answer"])

    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")
    
    finally:
        # 사용이 끝난 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)

else:
    st.info("좌측 상단에서 PDF 파일을 업로드해 주세요.")