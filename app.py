import streamlit as st

st.set_page_config(
    page_title="🎬 유튜브 댓글 분석 프로젝트",
    layout="wide",
    page_icon="📊"
)

# ─────────────────────────────────────────────
st.markdown("""
# 🎬 YouTube 댓글 분석 프로젝트 📊  
**누구나 쉽게 따라할 수 있는 실용형 데이터 리터러시 실습**  
(by **석리송**)

---

### 📚 프로젝트 소개

이 웹앱은 유튜브 영상의 댓글을 수집하여 다양한 방식으로 분석할 수 있는 실습용 프로젝트입니다.  
데이터 분석과 시각화를 통해 유튜브 콘텐츠에 대한 사용자 반응을 살펴볼 수 있어요.

- 유튜브 영상 링크만 입력하면 댓글 수집 가능
- 시간대별 댓글 추이, 좋아요 수 분석
- 자주 등장하는 단어 시각화(워드클라우드) 제공
- Streamlit Cloud에서 쉽게 실행 가능

---

### 🔑 YouTube API Key 발급 방법

1. [https://console.cloud.google.com/](https://console.cloud.google.com/) 접속 후 로그인  
2. 새로운 프로젝트 생성 (예: `youtube-analysis`)
3. 좌측 메뉴 → **API 및 서비스 > 라이브러리**로 이동  
4. **YouTube Data API v3** 검색 후 클릭 → "사용" 클릭  
5. 다시 좌측 메뉴 → **사용자 인증 정보 > 사용자 인증 정보 만들기 > API 키** 클릭  
6. 생성된 API 키를 복사하여 `.streamlit/secrets.toml`에 다음과 같이 저장합니다:

```toml
[youtube]
youtube_api_key = "여기에_발급받은_API_키_붙여넣기"

⚠️ 외부 공유 시 API 키는 노출되지 않도록 주의해주세요.
🚀 지금 바로 왼쪽 사이드바에서 원하는 분석기를 선택해보세요!
""")
