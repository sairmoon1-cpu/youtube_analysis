import streamlit as st
from googleapiclient.discovery import build
import re

# ✅ 샘플용 URL & API Key (선택)
SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
SAMPLE_API_KEY = "AIzaSyBVmINQWW1wfHQ4LwXwcC6a9eAtHU6A_ro"  # 제한적 공개 키

# 🔎 video ID 추출 함수
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 💬 댓글 수집 함수
def get_comments(video_id, api_key):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=1000,
            textFormat="plainText"
        ).execute()

        for item in response["items"]:
            text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(text)

    except Exception as e:
        st.error("❌ API 호출 중 오류가 발생했습니다.")
        st.code(str(e))

    return comments

# 🖥️ Streamlit 앱 UI
st.title("🎯 YouTube 댓글 수집기")

# 🔐 API 발급 방법 안내
with st.expander("📘 YouTube API Key 발급 방법 안내"):
    st.markdown("""
    1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
    2. 새 프로젝트를 생성합니다.
    3. `YouTube Data API v3`를 검색하고 **활성화**합니다.
    4. 좌측 메뉴에서 **사용자 인증 정보** → `API 키 만들기`
    5. 생성된 API 키를 아래 입력창에 붙여넣으세요.
    """)

# 📥 입력값
youtube_url = st.text_input("📺 YouTube 영상 URL 입력", value=SAMPLE_URL)
api_key = st.text_input("🔑 API 키 입력", type="password", value=SAMPLE_API_KEY)

# ▶️ 버튼
if st.button("댓글 수집 시작"):
    video_id = extract_video_id(youtube_url)

    if not video_id:
        st.warning("⚠️ 유효한 YouTube URL을 입력해주세요.")
        st.stop()

    with st.spinner("🔄 댓글 수집 중..."):
        comments = get_comments(video_id, api_key)

    if comments:
        st.success(f"✅ 댓글 {len(comments)}개가 수집되었습니다.")
        for i, comment in enumerate(comments, 1):
            st.write(f"💬 {i}. {comment}")
    else:
        st.warning("😥 댓글이 존재하지 않거나 수집할 수 없습니다.")
