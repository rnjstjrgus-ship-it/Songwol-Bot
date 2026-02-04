import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 모델 설정 (1.5 Flash로 안정성 확보)
# 2.5 Flash가 429(쿼터초과)면 이 녀석이 구원투수야!
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

# 2. UI 구성
st.title("🎀 송월 규정 요정 (1.5 Flash)")
st.caption(f"⚡ 현재 엔진: {MODEL_NAME}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

def handle_click(query):
    st.session_state.clicked_query = query

for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🧚"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

prompt = st.chat_input("궁금한 규정을 물어봐!")

if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧚"):
        with st.spinner("요정이 1.5 엔진으로 답변 만드는 중... ✨"):
            try:
                # [중요] 404 방지를 위해 v1beta 경로를 명확히 지정
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
                
                instruction = (
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 핵심만 요약해서 답변해줘. "
                    f"답변 끝에는 반드시 [Q: 질문] 형식으로 추천 질문 2개 달아줘. \n\n[규정]\n{rules_text}"
                )
                
                payload = {"contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]}
                
                response = requests.post(url, json=payload)
                
                # 404 에러나면 바로 알려주기
                if response.status_code == 404:
                    st.error("🚨 헉, 또 404 에러야! 모델명을 'gemini-1.5-flash-latest'로 바꿔야 할 수도 있어.")
                elif response.status_code == 429:
                    st.error("🚨 1.5 엔진도 1분 사용량 초과래... 조금만 쉬자!")
                else:
                    res_json = response.json()
                    if "candidates" in res_json:
                        full_res = res_json['candidates'][0]['content']['parts'][0]['text']
                        main_answer = full_res.split("[Q:")[0].strip()
                        st.markdown(main_answer)
                        st.session_state.messages.append({"role": "assistant", "content": main_answer})
                        
                        # (추천 질문 버튼 로직은 동일)
                        if "[Q:" in full_res:
                            raw_sug = full_res.split("[Q:")[1:]
                            sugs = [s.split("]")[0].strip() for s in raw_sug][:2]
                            st.write("---")
                            cols = st.columns(2)
                            for i, s in enumerate(sugs):
                                with cols[i]:
                                    st.button(f"🔍 {s}", on_click=handle_click, args=(s,), key=f"btn_{len(st.session_state.messages)}_{i}")
            except Exception as e:
                st.error(f"실행 오류: {str(e)}")
