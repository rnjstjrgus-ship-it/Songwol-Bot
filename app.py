import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# [방어막 1] 페이지 설정에서 에러 나면 그냥 무시하고 넘어가게 처리
try:
    st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")
except Exception:
    pass

# 1. API 키 로드
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets에 GEMINI_API_KEY를 넣어줘!")
    st.stop()

# 2. PDF 로드 함수 (캐싱 적용)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        return f"PDF 로드 실패: {str(e)}"

rules_text = load_rules()

# 3. UI 구성
st.title("🏢 송월 사내 규정 챗봇")
st.markdown("---")

# 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. 질문 답변 로직
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if "로드 실패" in rules_text:
            st.error(rules_text)
        else:
            try:
                # 구글 라이브러리로 호출
                response = model.generate_content(
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"
                )
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error("답변을 생성하지 못했습니다.")
            except Exception as e:
                st.error(f"구글 API 에러 발생: {str(e)}")
