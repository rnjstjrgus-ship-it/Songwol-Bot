import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

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

# 3. UI 구성
st.title("🏢 송월 사내 규정 챗봇")

# API 키 확인
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets에 GEMINI_API_KEY를 설정해주세요!")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 로그 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 답변 로직
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not rules_text:
            st.error("rules.pdf 파일을 읽지 못했습니다.")
        else:
            try:
                # 직접 API 호출 방식
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"
                        }]
                    }]
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                result = response.json()
                
                if "candidates" in result:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
                    st.error(f"API 오류: {error_msg}")
            except Exception as e:
                st.error(f"❌ 연결 실패: {e}")

# --- 코드의 끝 (이 주석까지 복사해줘!) ---
