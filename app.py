import streamlit as st
import requests
import os
from PyPDF2 import PdfReader

st.set_page_config(page_title="송월 사내 규정 챗봇", page_icon="🏢")

# ---------------- API KEY ----------------
api_key = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("❌ GEMINI_API_KEY를 Secrets 또는 환경변수에 설정해주세요!")
    st.stop()

# ---------------- PDF LOAD ----------------
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception:
        return None

rules_text = load_rules()

st.title("🏢 송월 사내 규정 챗봇")
st.info("사내 규정을 기반으로 답변해드립니다.")

if not rules_text:
    st.error("❌ rules.pdf 파일을 읽지 못했습니다.")
    st.stop()

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(ms
