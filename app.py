import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정 (최상단)
st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")

# 2. API 키 및 모델 설정
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets에 GEMINI_API_KEY를 넣어줘!")
    st.stop()

# 3. PDF 로드 함수 (캐싱)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = "".join([page.extract_text() for page in reader.pages])
        return text
    except Exception as e:
        return f"PDF 로드 실패: {str(e)}"

rules_text = load_rules()

# 4. UI 구성
st.title("🏢 송월 사내 규정 챗봇")
st.info("7800X3D 유저를 위한 정밀 답변 모드 ON 🚀")

# 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 질문 답변 로직
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if "로드 실패" in rules_text:
            st.error(rules_text)
        else:
            try:
                # 구글 라이브러리로 안전하게 호출
                response = model.generate_content(
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 친절하게 답변해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"
                )
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error("답변을 생성하지 못했습니다.")
                    
            except Exception as e:
                # 여기서 에러나면 100% 키 권한 문제임
                st.error(f"구글 AI 에러 발생: {str(e)}")
                if "API_KEY_INVALID" in str(e):
                    st.warning("키가 유효하지 않대. Secrets에 복사할 때 공백이 들어갔는지 봐줘!")
