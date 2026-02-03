import streamlit as st
import requests
import json
import os
from PyPDF2 import PdfReader

# 페이지 설정 (반드시 최상단)
st.set_page_config(page_title="송월 사내 규정 챗봇", page_icon="🏢")

# -----------------------------
# 1. Gemini API 키 불러오기
# -----------------------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY를 Secrets 또는 환경변수에 설정해주세요!")
    st.stop()

# -----------------------------
# 2. PDF 로드 (캐싱)
# -----------------------------
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")  # 깃허브 루트에 있어야 함
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        return None

rules_text = load_rules()

# -----------------------------
# 3. 기본 UI
# -----------------------------
st.title("🏢 송월 사내 규정 챗봇")
st.info("사내 규정을 기반으로 답변해드립니다.")

if not rules_text:
    st.error("❌ rules.pdf 파일을 읽지 못했습니다. 깃허브에 파일이 있는지 확인하세요.")
    st.stop()

# -----------------------------
# 4. 채팅 세션 초기화
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# 이전 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------
# 5. 질문 처리
# -----------------------------
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("규정 확인 중..."):
            try:
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}

                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"""너는 회사 사내 규정 전문가야.
아래 규정을 근거로만 답변하고, 없는 내용은 추측하지 마.

[사내 규정]
{rules_text}

[질문]
{prompt}
"""
                        }]
                    }]
                }
