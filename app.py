import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. 페이지 설정 (가장 먼저 호출!)
st.set_page_config(page_title="사내 규정 챗봇", icon="🏢")

# 2. API 설정
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"🚨 API 키 설정 에러! Secrets를 확인하세요. ({e})")
    st.stop()

# 3. PDF 읽기 함수 (캐싱 적용)
@st.cache_resource
def load_data():
    try:
        # 파일명이 반드시 rules.pdf 여야 함!
        reader = PdfReader("rules.pdf")
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        return full_text
    except Exception as e:
        st.error(f"🚨 PDF 읽기 실패! 'rules.pdf' 파일이 있는지 확인하세요. ({e})")
        return None

# 데이터 로드
data = load_data()

st.title("🏢 사내 규정 챗봇")
st.info("사내 규정 문서를 바탕으로 Gemini AI가 답변합니다.")

if data:
    # 4. 채팅 세션 관리
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 이전 대화 출력
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 5. 사용자 입력 및 답변 생성
    if prompt := st.chat_input("질문을 입력하세요 (예: 연차 규정 알려줘)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # 404 에러 방지를 위해 가장 범용적인 모델명 사용
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 프롬프트 구성
                full_prompt = f"너는 회사의 인사팀 직원이야. 아래의 사내 규정 내용을 바탕으로 질문에 친절하게 답해줘.\n\n[규정 내용]\n{data}\n\n[질문]\n{prompt}"
                
                response = model.generate_content(full_prompt)
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.warning("AI가 답변을 생성하지 못했습니다.")
            except Exception as e:
                st.error(f"❌ AI 답변 생성 중 오류 발생: {e}")
else:
    st.warning("PDF 데이터를 불러오지 못했습니다. 깃허브에 'rules.pdf'가 있는지 확인해주세요.")
