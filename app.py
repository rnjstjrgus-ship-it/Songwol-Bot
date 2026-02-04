import streamlit as st
import requests
from PyPDF2 import PdfReader

# 페이지 설정
st.set_page_config(page_title="송월 규정 요정", page_icon="🧚", layout="centered")

MODEL_NAME = "gemini-2.5-flash"

@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        return text.strip()
    except:
        return ""

# [핵심] 듀얼 키 리스트 생성
api_keys = [
    st.secrets.get("GEMINI_API_KEY_1"),
    st.secrets.get("GEMINI_API_KEY_2")
]
rules_text = load_rules()

st.write("### 🎀 송월 사내 규정 요정")
st.caption(f"⚡ 듀얼 엔진 가동 중 (2.5 Flash)")

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

prompt = st.chat_input("궁금한 규정을 말해줘!")

if st.session_state.clicked_query:
    prompt = st.session_state.clicked_query
    st.session_state.clicked_query = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🧚"):
        # [핵심] API 키를 순회하며 성공할 때까지 시도
        success = False
        for idx, key in enumerate(api_keys):
            if not key: continue # 키가 설정 안 되어 있으면 패스
            
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={key}"
                instruction = f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 친절하고 귀엽게 답변해줘. [규정] {rules_text} 답변 후에는 반드시 연관 질문 3개를 [Q: 질문] 형식으로 적어줘."
                payload = {"contents": [{"parts": [{"text": f"{instruction} 질문: {prompt}"}]}]}
                
                res = requests.post(url, json=payload)
                
                # 429(쿼터초과)면 다음 키로 넘어가고, 200(성공)이면 중단
                if res.status_code == 429:
                    st.warning(f"⚠️ {idx+1}번 엔진 과열! 보조 엔진으로 전환합니다...")
                    continue 
                
                res_json = res.json()
                if "candidates" in res_json:
                    full_response = res_json['candidates'][0]['content']['parts'][0]['text']
                    
                    # (기존 파싱 로직 동일)
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
                        cols = st.columns(len(suggestions))
                        for i, sug in enumerate(suggestions):
                            with cols[i]:
                                st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
                    
                    success = True
                    break # 성공했으니 루프 종료
            except:
                continue

        if not success:
            st.error("🚨 모든 엔진의 쿼터가 소진되었습니다. 잠시 후 다시 시도해주세요.")
