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

# 듀얼 키 리스트
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
        # [수정] spinner를 추가해서 답변 생성 중임을 표시!
        with st.spinner("🧚 요정이 규정집을 뒤적거리고 있어... 잠시만!"):
            success = False
            for idx, key in enumerate(api_keys):
                if not key: continue
                
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={key}"
                    instruction = f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 친절하고 귀엽게 답변해줘. [규정] {rules_text} 답변 후에는 반드시 연관 질문 3개를 [Q: 질문] 형식으로 적어줘."
                    payload = {"contents": [{"parts": [{"text": f"{instruction} 질문: {prompt}"}]}]}
                    
                    res = requests.post(url, json=payload)
                    
                    if res.status_code == 429:
                        # 첫 번째 키 실패 시 살짝 안내만 하고 다음 키로!
                        if idx == 0 and len(api_keys) > 1:
                            st.write("💡 1번 엔진 과열! 보조 엔진으로 갈아탈게!")
                        continue 
                    
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
                            cols = st.columns(len(suggestions))
                            for i, sug in enumerate(suggestions):
                                with cols[i]:
                                    st.button(f"🔍 {sug}", on_click=handle_click, args=(sug,), key=f"btn_{len(st.session_state.messages)}_{i}")
                        
                        success = True
                        break 
                except:
                    continue

            if not success:
                st.error("🚨 모든 엔진의 쿼터가 소진되었어... 구글이 형의 열정에 항복했네. ㅠㅠ")
