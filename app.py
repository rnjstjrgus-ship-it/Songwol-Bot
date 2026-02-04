import streamlit as st
import requests
import json
import re
from PyPDF2 import PdfReader

# 1. 모델 설정 (무조건 2.5 Flash)
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
st.title("🎀 송월 규정 요정 (Light Edition)")
st.caption(f"⚡ {MODEL_NAME} 스트리밍 모드 최적화")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

def handle_click(query):
    st.session_state.clicked_query = query

# 대화 내역 출력
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🧚"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 3. 질문 입력 처리
prompt = st.chat_input("궁금한 규정을 물어봐!")

if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧚"):
        def stream_gemini():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:streamGenerateContent?key={api_key}"
            instruction = (
                f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 핵심만 요약해서 심플하게 답변해줘. "
                f"원문을 길게 나열하지 마. 답변 후 맨 마지막에만 [Q: 질문] 형식으로 연관 질문 '2개'만 추가해줘. \n\n[규정]\n{rules_text}"
            )
            payload = {"contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]}
            
            response = requests.post(url, json=payload, stream=True)
            full_text = ""
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8').strip()
                    # 정규표현식으로 "text": "내용" 부분만 안전하게 추출
                    match = re.search(r'"text":\s*"(.*?)"', decoded)
                    if match:
                        content = match.group(1).encode().decode('unicode_escape')
                        full_text += content
                        # 질문 태그 전까지만 실시간으로 화면에 출력
                        if "[Q:" not in full_text:
                            yield content
            
            st.session_state.last_full_response = full_text

        # 스트리밍 출력
        final_answer = st.write_stream(stream_gemini)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

        # 연관 질문 버튼 생성 (2개 제한)
        full_res = st.session_state.get("last_full_response", "")
        if "[Q:" in full_res:
            raw_suggestions = full_res.split("[Q:")[1:]
            suggestions = [s.split("]")[0].strip() for s in raw_suggestions][:2]
            
            if suggestions:
                st.write("---")
                st.caption("✨ 요런 건 어때?")
                cols = st.columns(len(suggestions))
                for i, sug in enumerate(suggestions):
                    with cols[i]:
                        st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
