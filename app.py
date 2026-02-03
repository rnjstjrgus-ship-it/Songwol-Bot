import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. API 설정 (강제 버전 고정 버전)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    # 구버전(v1beta) 억까를 피하기 위해 최신 설정 적용
    genai.configure(api_key=api_key)
    
    # 모델 호출 시점을 최대한 늦추고, 최신 명칭인 'gemini-1.5-flash' 사용
    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 설정 에러: {e}")
    st.stop()

# 2. PDF 로드 (캐싱)
@st.cache_resource
def load_rules():
    try:
        reader = PdfReader("rules.pdf")
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content
        return text
    except Exception as e:
        return None

rules_text = load_rules()

st.title("🏢 송월 사내 규정 챗봇")

if not rules_text:
    st.error("🚨 'rules.pdf' 파일을 찾을 수 없습니다!")
    st.stop()

# 3. 채팅 UI
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("규정에 대해 물어보세요!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # 문서 내용을 먼저 주고 질문을 던지는 방식
            full_prompt = f"다음 사내 규정을 읽고 질문에 답해줘.\n\n[규정]\n{rules_text}\n\n[질문]\n{prompt}"
            
            # 답변 생성 (stream=False로 안정성 확보)
            response = model.generate_content(full_prompt)
            
            if response.text:
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            else:
                st.warning("AI가 답변을 생성하지 못했습니다.")
        except Exception as e:
            # 만약 여기서 또 404가 뜨면, 진짜 최후의 수단으로 모델명을 'gemini-pro'로 강제 변경
            st.error(f"❌ 오류 발생: {e}")
            st.info("이 에러가 반복되면, API 키 발급 시 'Gemini API'가 아닌 다른 서비스를 선택했는지 확인이 필요해!")
