import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 모델 설정 (1.5 Flash로 안정성 확보)
# 만약 1.5도 404 뜨면 'gemini-1.5-flash-latest'로 아래 이름만 바꿔줘!
MODEL_NAME = "gemini-1.5-flash" 

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

# 2. UI 구성 (귀염 뽀짝 유지)
st.title("🎀 송월 규정 요정")
st.caption(f"⚡ 현재 작동 엔진: {MODEL_NAME}")

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
        # 상태 메시지로 형을 안심시키기
        with st.spinner(f"요정이 {MODEL_NAME} 엔진을 예열 중이야... ✨"):
            try:
                # [핵심] 404 방지를 위한 URL 구조 (v1beta 사용)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
                
                instruction = (
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 핵심만 요약해서 심플하게 답변해줘. "
                    f"답변 끝에는 반드시 [Q: 질문] 형식으로 연관 질문 2개를 추가해줘. \n\n[규정]\n{rules_text}"
                )
                
                payload = {"contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]}
                
                response = requests.post(url, json=payload)
                
                # 에러 코드별 맞춤 대응
                if response.status_code == 404:
                    st.error(f"🚨 아직도 404 에러네! 모델명을 'gemini-1.5-flash-latest'로 바꿔서 다시 시도해볼게.")
                elif response.status_code == 429:
                    st.warning("🚨 형, 구글이 1분당 사용량 초과래! 30초만 쉬었다가 다시 눌러줘.")
                elif response.status_code == 200:
                    res_json = response.json()
                    if "candidates" in res_json:
                        full_res = res_json['candidates'][0]['content']['parts'][0]['text']
                        
                        # 답변과 버튼 분리
                        main_answer = full_res.split("[Q:")[0].strip()
                        st.markdown(main_answer)
                        st.session_state.messages.append({"role": "assistant", "content": main_answer})
                        
                        if "[Q:" in full_res:
                            raw_sug = full_res.split("[Q:")[1:]
                            sugs = [s.split("]")[0].strip() for s in raw_sug][:2]
                            st.write("---")
                            st.caption("✨ 요런 건 어때?")
                            cols = st.columns(2)
                            for i, s in enumerate(
