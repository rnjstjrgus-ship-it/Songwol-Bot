import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 모델 설정 (Gemini 2.5 Flash 전제)
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

# 2. UI 구성 (심플 & 귀염)
st.title("🎀 송월 규정 요정")
st.caption(f"⚡ {MODEL_NAME} 안정 모드 가동 중")

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
        # 답변 생성 중임을 알리는 스피너
        with st.spinner("요정이 규정집을 뒤적거리고 있어... ✨"):
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
                
                # 프롬프트 기강 잡기 (버튼 텍스트 유실 방지)
                instruction = (
                    f"너는 송월의 사내 규정 전문가야. 아래 규정을 바탕으로 사용자가 읽기 편하게 핵심만 요약해줘. "
                    f"답변 끝에는 반드시 [Q: 질문내용] 형식으로 연관 질문 2개를 넣어줘. 질문 내용은 구체적이어야 해. \n\n[규정]\n{rules_text}"
                )
                
                payload = {
                    "contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]
                }
                
                response = requests.post(url, json=payload)
                res_json = response.json()
                
                # 에러 핸들링 강화
                if response.status_code == 429:
                    st.error("🚨 1분 사용량 초과! (Rate Limit) 30초만 쉬었다가 다시 해줘.")
                elif "candidates" in res_json:
                    full_text = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # 답변과 추천 질문 분리 로직 보강
                    if "[Q:" in full_text:
                        main_answer = full_text.split("[Q:")[0].strip()
                        raw_suggestions = full_text.split("[Q:")[1:]
                        # '질문'이라는 단어만 나오지 않게 세밀하게 파싱
                        suggestions = [s.split("]")[0].replace("질문:", "").strip() for s in raw_suggestions][:2]
                    else:
                        main_answer = full_text
                        suggestions = []

                    st.markdown(main_answer)
                    st.session_state.messages.append({"role": "assistant", "content": main_answer})

                    if suggestions:
                        st.write("---")
                        st.caption("✨ 요런 건 어때?")
                        cols = st.columns(2)
                        for i, sug in enumerate(suggestions):
                            if sug: # 내용이 있을 때만 버튼 생성
                                with cols[i]:
                                    st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
                else:
                    st.error(f"🚨 구글 서버 응답 실패: {res_json.get('error', {}).get('message', '알 수 없는 이유')}")
            
            except Exception as e:
                st.error(f"시스템 오류 발생: {str(e)}")
