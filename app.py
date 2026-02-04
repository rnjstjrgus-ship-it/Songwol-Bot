import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 모델 설정 (형의 말대로 오직 2.5 Flash!)
MODEL_NAME = "gemini-2.5-flash" 

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

# 2. UI 구성
st.title("🎀 송월 규정 요정")
st.caption(f"⚡ Pure 2.5 Flash Engine 가동 중")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

def handle_click(query):
    st.session_state.clicked_query = query

# 대화 기록 출력
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🧚"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 3. 질문 처리
prompt = st.chat_input("궁금한 규정을 물어봐!")

if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧚"):
        with st.spinner(f"요정이 {MODEL_NAME}으로 규정 분석 중... ✨"):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
                instruction = (
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 핵심만 요약해서 답변해줘. "
                    f"답변 끝에는 반드시 [Q: 질문] 형식으로 연관 질문 2개를 추가해줘. \n\n[규정]\n{rules_text}"
                )
                payload = {"contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]}
                
                response = requests.post(url, json=payload)
                
                if response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json:
                        full_res = res_json['candidates'][0]['content']['parts'][0]['text']
                        main_answer = full_res.split("[Q:")[0].strip()
                        st.markdown(main_answer)
                        st.session_state.messages.append({"role": "assistant", "content": main_answer})
                        
                        if "[Q:" in full_res:
                            raw_sug = full_res
