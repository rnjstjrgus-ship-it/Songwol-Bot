import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 모델 설정 (기본 전제: Gemini 2.5 Flash)
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
st.caption(f"⚡ {MODEL_NAME} 스트리밍 모드 가동 중")

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
        # [핵심] 스트리밍 데이터를 실시간으로 받아내는 생성기 함수
        def stream_gemini():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:streamGenerateContent?key={api_key}"
            instruction = (
                f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변하되, "
                f"원문을 그대로 나열하지 말고 핵심만 요약해서 심플하게 답변해줘. "
                f"답변 끝에는 반드시 [Q: 질문] 형식으로 연관 질문 3개를 달아줘. \n\n[규정]\n{rules_text}"
            )
            payload = {"contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]}
            
            response = requests.post(url, json=payload, stream=True)
            full_text = ""
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8').strip()
                    if decoded.startswith('"text": "'):
                        # 텍스트 데이터만 쏙 골라내기
                        content = decoded.split('"text": "')[1].split('"')[0].replace("\\n", "\n")
                        full_text += content
                        # 추천 질문 태그 전까지만 화면에 실시간 노출
                        if "[Q:" not in full_text:
                            yield content
            
            # 마지막에 추천 질문 파싱을 위해 전체 텍스트 저장용
            st.session_state.last_full_response = full_text

        # 스트리밍 출력 실행
        final_answer = st.write_stream(stream_gemini)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})

        # 연관 질문 버튼 생성 (답변 완료 후)
        full_res = st.session_state.get("last_full_response", "")
        if "[Q:" in full_res:
            suggestions = [p.split("]")[0].strip() for p in full_res.split("[Q:")[1:]]
            if suggestions:
                st.write("---")
                st.caption("✨ 요정의 추천 질문!")
                cols = st.columns(len(suggestions))
                for i, sug in enumerate(suggestions):
                    with cols[i]:
                        st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
