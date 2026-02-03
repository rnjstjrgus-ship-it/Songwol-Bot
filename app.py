import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정
st.set_page_config(page_title="송월 사내 규정 챗봇", layout="centered")

# 2. API 설정 및 모델 기강 잡기
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # 최신 라이브러리에서는 'models/'를 붙이는 게 정석이야
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 설정 에러: {e}")
    st.stop()

# 3. PDF 로드 (캐싱)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return None

rules_text = load_rules()

st.title("🏢 송월 사내 규정 챗봇")

if not rules_text:
    st.error("🚨 'rules.pdf' 파일을 찾을 수 없어! 깃허브에 잘 올라가 있는지 확인해줘.")
    st.stop()

# 4. 채팅 세션 관리
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 5. 질문 답변
if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            # 럭키비키하게 답변 생성
            full_prompt = f"너는 사내 규정 전문가야. 아래 내용을 바탕으로 답변해줘:\n\n{rules_text}\n\n질문: {prompt}"
            response = model.generate_content(full_prompt)
            
            st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"❌ 최종 에러 발생: {e}")
            st.info("이 에러가 뜨면 'Manage app'에서 'Reboot'을 꼭 눌러줘!")
