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
st.caption(f"⚡ {MODEL_NAME} 엔진 가동 중")

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
        # [핵심] 답변 시작 전 상태 알림 표시
        status_text = st.empty()
        status_text.markdown("요정이 규정을 읽고 답변을 생각 중이야... 잠시만! ✨")
        
        full_response = ""
        message_placeholder = st.empty() # 답변이 들어갈 빈 공간

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:streamGenerateContent?key={api_key}"
            instruction = (
                f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 핵심만 요약해서 심플하게 답변해줘. "
                f"답변 후 맨 마지막에만 [Q: 질문] 형식으로 연관 질문 2개만 추가해줘. \n\n[규정]\n{rules_text}"
            )
            payload = {"contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]}
            
            response = requests.post(url, json=payload, stream=True)
            
            for line in response.iter_lines():
                if line:
                    decoded = line.decode('utf-8').strip()
                    # 스트리밍 JSON에서 텍스트 조각만 추출
                    if decoded.startswith('{') or '"text":' in decoded:
                        try:
                            # 텍스트만 포함된 행인지 확인
                            if '"text":' in decoded:
                                content = decoded.split('"text": "')[1].split('"')[0].replace("\\n", "\n")
                                if content:
                                    if not full_response: # 첫 글자가 나오면 상태 메시지 삭제
                                        status_text.empty()
                                    
                                    full_response += content
                                    # 연관 질문 나오기 전까지만 실시간 노출
                                    display_answer = full_response.split("[Q:")[0]
                                    message_placeholder.markdown(display_answer + "▌")
                        except:
                            continue

            # 최종 답변 확정
            final_main_answer = full_response.split("[Q:")[0].strip()
            message_placeholder.markdown(final_main_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_main_answer})
            st.session_state.last_full_response = full_response

            # 연관 질문 버튼 생성
            if "[Q:" in full_response:
                raw_suggestions = full_response.split("[Q:")[1:]
                suggestions = [s.split("]")[0].strip() for s in raw_suggestions][:2]
                
                if suggestions:
                    st.write("---")
                    st.caption("✨ 궁금해할 것 같아서 준비했어!")
                    cols = st.columns(2)
                    for i, sug in enumerate(suggestions):
                        with cols[i]:
                            st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
        
        except Exception as e:
            status_text.empty()
            st.error(f"으악! 통신 중에 문제가 생겼어: {str(e)}")
