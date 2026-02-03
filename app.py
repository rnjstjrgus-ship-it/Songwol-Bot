import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="송월 사내 규정 챗봇", layout="centered")

# 2. API 설정 및 모델 기강 잡기
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets에 GEMINI_API_KEY를 설정해주세요!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. PDF 로드 (캐싱)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except Exception as e:
        return None

rules_text = load_rules()

st.title("🏢 송월 사내 규정 챗봇")

if not rules_text:
    st.error("🚨 'rules.pdf' 파일을 찾을 수 없습니다! 깃허브를 확인해주세요.")
    st.stop()

# 4. 채팅 세션 관리
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
        try:
            # 404 에러 방지를 위한 가장 표준적인 모델 호출
            # 만약 이게 안되면 'gemini-1.5-flash-latest'로 자동 전환 시도
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                model = genai.GenerativeModel('gemini-pro')
            
            full_prompt = f"당신은 사내 규정 전문가입니다. 아래 내용을 바탕으로 답변하세요.\n\n[내용]\n{rules_text}\n\n[질문]\n{prompt}"
            
            response = model.generate_content(full_prompt)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.error("AI가 답변을 생성하지 못했습니다.")
        except Exception as e:
            st.error(f"❌ 최종 에러 발생: {e}")
            st.info("이 에러가 계속되면 Google AI Studio에서 새로운 API 키를 다시 한 번만 발급받아보세요.")
