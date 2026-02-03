import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정 (웹사이트 제목)
st.set_page_config(page_title="송월 규정 챗봇", page_icon="🤖")
st.title("🏢 사내 규정 무엇이든 물어보세요!")
st.info("이 챗봇은 사내 규정 PDF를 바탕으로 답변합니다.")

# 2. 보안을 위해 설정에서 API 키를 가져옴
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Streamlit 설정에서 API 키를 등록해주세요!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. PDF 파일 읽기 함수 (파일 이름은 무조건 rules.pdf로!)
@st.cache_resource
def load_pdf_content():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"rules.pdf 파일을 찾을 수 없거나 읽을 수 없습니다: {e}")
        return None

pdf_text = load_pdf_content()
model = genai.GenerativeModel("gemini-1.5-flash")

# 4. 채팅 메시지 저장용 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 기존 대화 표시
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. 채팅창 입력 로직
if prompt := st.chat_input("연차 규정이나 복지에 대해 물어보세요!"):
    # 사용자 질문 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 답변 생성
    with st.chat_message("assistant"):
        with st.spinner("규정을 확인하는 중..."):
            # PDF 내용과 질문을 섞어서 AI에게 전달
            full_prompt = f"당신은 사내 규정 안내 챗봇입니다. 아래 제공된 규정 내용을 바탕으로만 답변하세요. 모르는 내용은 모른다고 하세요.\n\n[규정 내용]\n{pdf_text}\n\n[사용자 질문]\n{prompt}"
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})
