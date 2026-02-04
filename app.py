import streamlit as st
import requests
import json
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
st.title("🎀 송월 규정 요정")
st.caption(f"⚡ {MODEL_NAME} 안정화 버전 가동 중")

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
        # [핵심] 무한 로딩 방지용 스피너 등장!
        with st.spinner("요정이 규정을 꼼꼼히 읽고 있어... 잠시만 기다려줘! ✨"):
            try:
                # 스트리밍 대신 일반 생성 API 사용 (더 안정적임)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
                
                instruction = (
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 핵심만 요약해서 심플하게 답변해줘. "
                    f"답변 후 맨 마지막에만 [Q: 질문] 형식으로 연관 질문 2개만 추가해줘. \n\n[규정]\n{rules_text}"
                )
                
                payload = {
                    "contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]
                }
                
                response = requests.post(url, json=payload)
                res_json = response.json()
                
                if "candidates" in res_json:
                    full_response = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # 답변과 추천 질문 분리
                    if "[Q:" in full_response:
                        main_answer = full_response.split("[Q:")[0].strip()
                        raw_suggestions = full_response.split("[Q:")[1:]
                        suggestions = [s.split("]")[0].strip() for s in raw_suggestions][:2]
                    else:
                        main_answer = full_response
                        suggestions = []

                    # 답변 출력
                    st.markdown(main_answer)
                    st.session_state.messages.append({"role": "assistant", "content": main_answer})

                    # 연관 질문 버튼
                    if suggestions:
                        st.write("---")
                        st.caption("✨ 이런 것도 궁금할 것 같아!")
                        cols = st.columns(2)
                        for i, sug in enumerate(suggestions):
                            with cols[i]:
                                st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
                else:
                    st.error("구글 서버가 대답을 못 하고 있어. 잠시 후 다시 시도해줘!")
                    
            except Exception as e:
                st.error(f"으악! 에러가 났어: {str(e)}")
