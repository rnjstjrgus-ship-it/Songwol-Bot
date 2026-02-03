import streamlit as st
import requests
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

# 2. 모델 및 데이터 로드
MODEL_NAME = "gemini-2.0-flash"  # 형 키에 맞춰서 2.0으로 기강 잡음

@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        return text.strip()
    except:
        return ""

api_key = st.secrets.get("GEMINI_API_KEY")
rules_text = load_rules()

# 3. UI 및 세션 관리
st.title("🏢 송월 사내 규정 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

# 버튼 클릭 시 호출될 함수
def handle_click(query):
    st.session_state.clicked_query = query

# 대화 내역 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 입력 처리 (채팅창 입력 OR 버튼 클릭)
prompt = st.chat_input("규정에 대해 물어보세요!")

# 버튼 클릭 시 prompt를 업데이트
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
            
            # 지시사항: 답변 뒤에 반드시 [Q: 질문] 형식으로 추천 질문을 달라고 함
            instruction = (
                f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘.\n\n"
                f"[규정]\n{rules_text}\n\n"
                "답변이 끝나면 반드시 사용자가 이
