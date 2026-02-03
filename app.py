import streamlit as st
import requests
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

# 2. 모델 설정 (Gemini 2.5 Flash가 출시됐으니 최신 사양으로!)
MODEL_NAME = "gemini-2.0-flash" 

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

# 3. UI 및 세션 관리
st.title("🏢 송월 사내 규정 챗봇")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

def handle_click(query):
    st.session_state.clicked_query = query

# 대화 내역 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 입력 처리
prompt = st.chat_input("규정에 대해 물어보세요!")

if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
            instruction = f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘. [규정] {rules_text} 답변 후에는 반드시 연관 질문 3개를 [Q: 질문] 형식으로 적어줘."
            
            payload = {
                "contents": [{"parts": [{"text": f"{instruction} 질문: {prompt}"}]}]
            }
            
            res = requests.post(url, json=payload)
            res_json = res.json()
            
            if "candidates" in res_json:
                full_response = res_json['candidates'][0]['content']['parts'][0]['text']
                
                # 답변과 추천 질문 분리
                if "[Q:" in full_response:
                    main_answer = full_response.split("[Q:")[0].strip()
                    suggestions = [p.split("]")[0].strip() for p in full_response.split("[Q:")[1:]]
                else:
                    main_answer = full_response
                    suggestions = []

                st.markdown(main_answer)
                st.session_state.messages.append({"role": "assistant", "content": main_answer})

                if suggestions:
                    st.write("---")
                    st.caption("💡 이런 질문은 어떠세요?")
                    cols = st.columns(len(suggestions))
                    for i, sug in enumerate(suggestions):
                        with cols[i]:
                            st.button(sug, on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
            else:
                st.error("답변 생성 실패. 쿼터 초과 여부를 확인해줘.")
        except Exception as e:
            st.error(f"에러 발생: {e}")
