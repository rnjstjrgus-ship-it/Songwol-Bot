# 1. 페이지 설정 (반드시 import 바로 다음에!)
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

import json
from PyPDF2 import PdfReader

# 2. PDF 로드 (캐싱)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    except Exception:
        return None

rules_text = load_rules()

# 3. UI 및 API 설정
st.title("🏢 송월 사내 규정 챗봇")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets에 GEMINI_API_KEY를 넣어줘!")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# 채팅 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 메인 로직
if prompt := st.chat_input("규정에 대해 질문해봐!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not rules_text:
            st.error("rules.pdf를 못 읽었어. 파일 확인해봐!")
        else:
            try:
                # 직접 API 호출 (404 방지용)
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{"text": f"규정:\n{rules_text}\n\n질문: {prompt}"}]
                    }]
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                result = response.json()
                
                if "candidates" in result:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"API 에러: {result.get('error', {}).get('message', '알 수 없는 오류')}")
            except Exception as e:
                st.error(f"연결 실패: {e}")
