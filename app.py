import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. API 설정 및 모델 로드 함수
def initial_setup():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # 가장 안정적인 최신 플래시 모델 명칭 사용
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        st.error(f"⚠️ 설정 오류: {e}")
        return None

# 2. PDF 읽기 함수 (캐싱)
@st.cache_resource
def load_pdf_data():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"⚠️ PDF 파일('rules.pdf')을 읽지 못했습니다: {e}")
        return None

# 앱 시작
model = initial_setup()
pdf_content = load_pdf_data()

st.title("🏢 사내 규정 챗봇")

if not model or not pdf_content:
    st.warning("설정 또는 PDF 파일에 문제가 있어 앱을 시작할 수 없습니다.")
    st.stop()

# 3. 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 로그 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 채팅 입력 및 답변 생성
if prompt := st.chat_input("질문을 입력해 보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 문서 내용과 질문을 결합하여 전달
            full_prompt = f"당신은 사내 규정 전문가입니다. 아래 내용을 바탕으로 답변하세요.\n\n내용:\n{pdf_content}\n\n질문: {prompt}"
            response = model.generate_content(full_prompt)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI가 대답을 생성하지 못했습니다.")
        except Exception as e:
            # 여기서 404가 또 뜨면 모델명을 'gemini-pro'로 바꿔야 함
            st.error(f"❌ AI 오류 발생: {e}")
