import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="사내 규정 챗봇", icon="🏢")
st.title("🏢 사내 규정 무엇이든 물어보세요!")

# 2. API 키 설정 (Secrets에서 가져오기)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("API 키 설정이 잘못되었습니다. Secrets를 확인해주세요.")
    st.stop()

# 3. PDF 파일 읽기 함수
@st.cache_resource
def load_pdf():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"PDF 파일을 읽을 수 없습니다: {e}")
        return None

pdf_text = load_pdf()

# 4. 챗봇 인터페이스
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # PDF 내용을 프롬프트에 포함
            full_prompt = f"다음은 사내 규정 문서 내용이야:\n\n{pdf_text}\n\n위 내용을 바탕으로 질문에 답해줘: {prompt}"
            
            response = model.generate_content(full_prompt)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI가 답변을 생성하지 못했습니다.")
        except Exception as e:
            st.error(f"에러가 발생했습니다: {e}")
