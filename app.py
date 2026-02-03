import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. API 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("API 키 에러!")
    st.stop()

# 2. PDF 읽기 (캐싱)
@st.cache_resource
def load_data():
    reader = PdfReader("rules.pdf")
    return "".join([p.extract_text() for p in reader.pages])

data = load_data()
st.title("🏢 사내 규정 챗봇")

# 3. 채팅 UI
if "msgs" not in st.session_state: st.session_state.msgs = []
for m in st.session_state.msgs:
    with st.chat_message(m["role"]): st.write(m["content"])

if p := st.chat_input("질문하세요"):
    st.session_state.msgs.append({"role": "user", "content": p})
    with st.chat_message("user"): st.write(p)
    
    with st.chat_message("assistant"):
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(f"내용:\n{data}\n\n질문: {p}")
        st.write(res.text)
        st.session_state.msgs.append({"role": "assistant", "content": res.text})
