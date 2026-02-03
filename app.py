import streamlit as st
import requests
import json
from PyPDF2 import PdfReader

# 1. 페이지 설정 (최상단 기강 잡기)
try:
    st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")
except:
    pass

# 2. PDF 로드 함수 (캐싱)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        return f"PDF 로드 실패: {str(e)}"

# 3. 데이터 준비
api_key = st.secrets.get("GEMINI_API_KEY")
rules_text = load_rules()

st.title("🏢 송월 사내 규정 챗봇")
st.markdown("---")

# 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 답변 로직 (v1 주소 직접 호출 방식)
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not api_key:
            st.error("Secrets에 GEMINI_API_KEY가 없습니다!")
        elif "로드 실패" in rules_text:
            st.error(rules_text)
        else:
            try:
                # [핵심] v1beta가 아닌 안정화된 v1 주소로 직접 꽂아버리기
                url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
                headers = {'Content-Type': 'application/json'}
                payload = {
                    "contents": [{
                        "parts": [{"text": f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"}]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=payload)
                result = response.json()
                
                # 결과 확인
                if "candidates" in result:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    # 구글이 뱉은 에러 메시지 그대로 보여주기
                    error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
                    st.error(f"구글 API 에러: {error_msg}")
                    with st.expander("에러 상세 로그 (이거 보여주면 바로 해결 가능)"):
                        st.json(result)
            except Exception as e:
                st.error(f"연결 에러 발생: {str(e)}")
