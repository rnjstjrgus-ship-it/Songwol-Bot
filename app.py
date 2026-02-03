import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. API 설정 (페이지 설정 코드 생략해서 에러 원천 차단)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"API 키 확인 필요: {e}")
    st.stop()

# 2. PDF 읽기 (캐싱)
@st.cache_resource
def load_pdf_data():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return None

data = load_pdf_data()

# 3. UI 구성
st.title("🏢 사내 규정 챗봇")

if data is None:
    st.error("🚨 'rules.pdf' 파일을 찾을 수 없습니다! 깃허브에 파일이 있는지 확인해주세요.")
    st.stop()

# 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 입력 및 답변
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 모델 명칭을 가장 안전한 'gemini-1.5-flash'로 고정
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"아래 규정 내용을 바탕으로 답해줘:\n\n{data}\n\n질문: {prompt}"
            
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"AI 오류 발생: {e}")
