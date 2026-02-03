import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 페이지 설정 (최상단)
try:
    st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")
except:
    pass

# 2. 모델 설정 (형이 말한 2.5 Flash로 기강 잡음)
MODEL_NAME = "gemini-2.5-flash"

# 3. PDF 로드 함수 (캐싱 적용)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        return f"PDF 로드 실패: {str(e)}"

api_key = st.secrets.get("GEMINI_API_KEY")
rules_text = load_rules()

st.title("🏢 송월 사내 규정 챗봇")
st.info(f"현재 엔진: {MODEL_NAME} 가동 중 🚀")
st.markdown("---")

# 채팅 세션 기록 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 답변 로직
if prompt := st.chat_input("규정에 대해 무엇이든 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not api_key:
            st.error("Secrets에 API 키가 설정되지 않았어!")
        elif "로드 실패" in rules_text:
            st.error(rules_text)
        else:
            try:
                # v1beta 주소가 최신 모델 대응이 가장 확실함
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{"text": f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"}]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                result = response.json()
                
                if "candidates" in result:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    # 할당량 초과나 모델명 오류 시 에러 출력
                    error_msg = result.get('error', {}).get('message', '응답 생성 오류')
                    st.error(f"구글 API 에러: {error_msg}")
                    with st.expander("디버깅용 상세 로그"):
                        st.json(result)
            except Exception as e:
                st.error(f"서버 연결 에러: {str(e)}")
