import streamlit as st
import requests
from PyPDF2 import PdfReader

# [드레스업 1] 페이지 설정 - 브라우저 탭에 귀여운 아이콘과 이름 표시
st.set_page_config(page_title="송월 규정 요정", page_icon="🧚", layout="centered")

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

# [드레스업 2] 상단 꾸미기
st.write("### 🎀 송월 사내 규정 요정")
st.caption(f"✨ 최신형 {MODEL_NAME} 엔진이 형을 도와줄 거야!")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "clicked_query" not in st.session_state:
    st.session_state.clicked_query = None

def handle_click(query):
    st.session_state.clicked_query = query

# [드레스업 3] 말풍선에 귀여운 아이콘 넣기
for message in st.session_state.messages:
    # 유저는 '👤', 봇은 '🤖' 또는 '🧚' 아이콘 사용
    avatar = "👤" if message["role"] == "user" else "🧚"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 3. 질문 입력 처리
prompt = st.chat_input("궁금한 규정을 말해줘! (예: 휴가, 복지)")

if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧚"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
            instruction = f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 친절하고 귀엽게 답변해줘. [규정] {rules_text} 답변 후에는 반드시 연관 질문 3개를 [Q: 질문] 형식으로 적어줘."
            
            payload = {
                "contents": [{"parts": [{"text": f"{instruction} 질문: {prompt}"}]}]
            }
            
            res = requests.post(url, json=payload)
            res_json = res.json()
            
            if "candidates" in res_json:
                full_response = res_json['candidates'][0]['content']['parts'][0]['text']
                
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
                    st.caption("✨ 요런 건 어때? 눌러봐!")
                    # [드레스업 4] 버튼 디자인 강조
                    cols = st.columns(len(suggestions))
                    for i, sug in enumerate(suggestions):
                        btn_key = f"btn_{len(st.session_state.messages)}_{i}"
                        with cols[i]:
                            st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=btn_key)
            else:
                st.error("힝... 답변 생성에 실패했어. 쿼터 확인해봐!")
        except Exception as e:
            st.error(f"으악 에러 발생! : {str(e)}")
