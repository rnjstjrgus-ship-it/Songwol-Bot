import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# [순위 0] 무조건 이 코드가 가장 먼저 실행되어야 함! (빈칸이나 주석 제외 첫 줄)
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

# 1. API 키 확인 (Secrets에서 가져오기)
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets에 'GEMINI_API_KEY'를 설정해주세요!")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# 2. PDF 로드 (캐싱 적용)
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
st.info("7800X3D급 정밀도로 사내 규정을 답변해 드립니다. 🚀")

# 채팅 세션 관리 (기존 대화 기억용)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 답변 로직 (직접 API 호출 방식)
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not rules_text:
            st.error("rules.pdf 파일을 읽지 못했습니다. 깃허브 저장소에 파일이 있는지 확인해주세요.")
        else:
            try:
                # 라이브러리 버전 타지 않는 직접 POST 호출 방식
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
                    # 상세 에러 메시지 출력 (디버깅용)
                    error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
                    st.error(f"API 오류 발생: {error_msg}")
            except Exception as e:
                st.error(f"❌ 연결 실패: {e}")
