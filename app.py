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

# 2. UI 구성 (귀염 뽀짝 유지)
st.title("🎀 송월 규정 요정 (Speed Edition)")
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
        # 스트리밍을 위한 빈 공간 생성
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # 스트리밍 API 호출 주소 (streamGenerateContent)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:streamGenerateContent?key={api_key}"
            
            # [기강잡기] 심플 답변 + 파생 질문 형식 지정
            instruction = (
                f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변하되, "
                f"절대 원문을 그대로 나열하지 말고 사용자가 한눈에 알 수 있게 핵심만 요약해서 심플하게 답변해줘. "
                f"답변 끝에는 반드시 [Q: 질문] 형식으로 연관 질문 3개를 달아줘. \n\n[규정]\n{rules_text}"
            )
            
            payload = {
                "contents": [{"parts": [{"text": f"{instruction}\n\n질문: {prompt}"}]}]
            }
            
            # 스트리밍 요청 처리
            response = requests.post(url, json=payload, stream=True)
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8').lstrip(" ,")
                    # 구글 스트리밍 데이터 파싱 (SSE 방식과 유사)
                    if decoded_line.startswith('{"candidates"'):
                        data = json.loads(decoded_line)
                        content = data['candidates'][0]['content']['parts'][0]['text']
                        full_response += content
                        # 중간 답변 표시 (연관 질문 제외하고 먼저 보여주기)
                        display_text = full_response.split("[Q:")[0]
                        message_placeholder.markdown(display_text + "▌")

            # 최종 답변 확정
            final_main_answer = full_response.split("[Q:")[0].strip()
            message_placeholder.markdown(final_main_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_main_answer})

            # 연관 질문 버튼 생성
            if "[Q:" in full_response:
                suggestions = [p.split("]")[0].strip() for p in full_response.split("[Q:")[1:]]
                if suggestions:
                    st.write("---")
                    st.caption("✨ 요정의 추천 질문!")
                    cols = st.columns(len(suggestions))
                    for i, sug in enumerate(suggestions):
                        with cols[i]:
                            st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
                            
        except Exception as e:
            st.error(f"으악! 스트리밍 중 사고 발생: {str(e)}")
