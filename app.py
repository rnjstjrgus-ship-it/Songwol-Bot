import streamlit as st
import requests
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

# 2. 모델 및 데이터 로드
MODEL_NAME = "gemini-2.0-flash"

@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        return text.strip()
    except: return ""

api_key = st.secrets.get("GEMINI_API_KEY")
rules_text = load_rules()

# 3. UI 및 세션 관리
st.title("🏢 송월 사내 규정 챗봇")
if "messages" not in st.session_state:
    st.session_state.messages = []
# 버튼 클릭으로 입력된 질문을 처리하기 위한 변수
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

# 대화 내역 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 파생 질문 버튼 처리 함수
def handle_click(query):
    st.session_state.clicked_query = query

# 5. 질문 입력 (채팅창 또는 버튼 클릭)
prompt = st.chat_input("규정에 대해 물어보세요!")
if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
            # [핵심] 프롬프트에 파생 질문을 특정 형식으로 달라고 명령함
            system_instruction = (
                f"규정:\n{rules_text}\n\n"
                "너는 사내 규정 전문가야. 답변 마지막에 사용자가 궁금해할 법한 '연관 질문' 3개를 "
                "반드시 [Q: 질문내용] 형식으로 작성해줘."
            )
            
            payload = {"contents": [{"parts": [{"text": f"{system_instruction}\n\n질문:
