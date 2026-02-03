import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 최상단 설정 (에러 방지용)
st.set_page_config(page_title="사내 규정 챗봇")

# 2. API 설정
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secrets에 GEMINI_API_KEY를 설정해주세요!")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 3. PDF 데이터 로드 (캐싱)
@st.cache_resource
def get_pdf_text():
    try:
        reader = PdfReader("rules.pdf")
        return "".join([page.extract_text() for page in reader.pages])
    except Exception as e:
        st.error(f"PDF 로드 실패: {e}")
        return None

rules_context = get_pdf_text()

# 4. UI 및 채팅 로직
st.title("🏢 사내 규정 챗봇")

if rules_context:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 채팅 출력
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 입력창
    if user_input := st.chat_input("규정에 대해 물어보세요"):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            try:
                # 여기서 모델명을 'gemini-1.5-flash'로 호출 (가장 안정적)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"너는 인사팀 전문가야. 아래 규정을 참고해서 답해줘.\n\n[규정]\n{rules_context}\n\n[질문]\n{user_input}"
                
                response = model.generate_content(prompt)
                ans = response.text
                
                st.write(ans)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error(f"에러 발생: {e}")
                st.info("이 에러가 404라면, 'Manage app' 메뉴에서 'Delete app' 후 다시 생성하는 게 빠를 수 있어.")
