import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. API 설정 및 모델 로드 (가장 호환성 높은 명칭 사용)
def initial_setup():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # 1.5-flash가 에러나면 가장 기본인 'gemini-pro'가 정답!
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"⚠️ 설정 오류: {e}")
        return None

# 2. PDF 읽기 함수
@st.cache_resource
def load_pdf_data():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        st.error(f"⚠️ PDF 파일('rules.pdf') 확인 필요: {e}")
        return None

# 앱 시작
model = initial_setup()
pdf_content = load_pdf_data()

st.title("🏢 사내 규정 챗봇")

if not model or not pdf_content:
    st.warning("설정 또는 PDF 파일 로드 중 문제가 발생했습니다.")
    st.stop()

# 3. 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 답변 생성
if prompt := st.chat_input("질문을 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 문서 내용과 질문 결합
            full_prompt = f"당신은 사내 규정 전문가입니다. 아래 내용을 바탕으로만 답변하세요.\n\n내용:\n{pdf_content}\n\n질문: {prompt}"
            response = model.generate_content(full_prompt)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI가 답변을 생성하지 못했습니다.")
        except Exception as e:
            st.error(f"❌ 최종 에러 발생: {e}")
            st.info("이 에러가 계속되면 구글 AI 스튜디오에서 API 키를 새로 발급받는 것을 추천합니다.")
