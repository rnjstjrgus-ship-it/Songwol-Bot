import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정 (최상단)
try:
    st.set_page_config(page_title="송월 사내 규정 챗봇", icon="🏢")
except:
    pass

# 2. API 키 및 모델 설정
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # 모델 설정을 v1 기반 안정화 버전으로 고정
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
st.markdown("---")

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
                # 가장 정석적인 generate_content 호출 (버전 자동 선택)
                response = model.generate_content(
                    f"너는 사내 규정 전문가야. 아래 규정을 바탕으로 답변해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"
                )
                
                if response and response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error("구글 API가 답변을 생성하지 못했습니다. (Safety filters 등)")
            except Exception as e:
                # 에러 발생 시 로그 상세 출력
                st.error(f"구글 API 에러 발생: {str(e)}")
