import streamlit as st
import requests
from PyPDF2 import PdfReader

# 1. 제목부터 띄우기 (이게 안 나오면 서버 문제임)
st.title("🏢 송월 사내 규정 챗봇")

# 2. PDF 읽기 (에러 방지용 try-except)
def get_rules():
    try:
        reader = PdfReader("rules.pdf")
        return "".join([p.extract_text() for p in reader.pages])
    except:
        return "PDF를 찾을 수 없습니다."

rules = get_rules()

# 3. API 키 체크
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.warning("Secrets에 API 키가 없습니다.")
    st.stop()

# 4. 채팅창
if prompt := st.chat_input("질문하세요"):
    st.chat_message("user").write(prompt)
    
    # 직접 호출
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": f"규정: {rules}\n\n질문: {prompt}"}]}]}
    
    try:
        res = requests.post(url, json=payload)
        ans = res.json()['candidates'][0]['content']['parts'][0]['text']
        st.chat_message("assistant").write(ans)
    except Exception as e:
        st.error(f"에러: {e}")
