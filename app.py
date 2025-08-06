import streamlit as st
from googleapiclient.discovery import build
import re

# 샘플 값
SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
SAMPLE_API_KEY = "AIzaSyBVmINQWW1wfHQ4LwXwcC6a9eAtHU6A_ro"

# ---------- 유틸 함수 ----------

def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_comments(video_id, api_key, max_comments=100):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    next_page_token = None

    while True:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            pageToken=next_page_token,
            order="relevance",
            textFormat="plainText"
        ).execute()

        for item in response["items"]:
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            comments.append(snippet["textDisplay"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token or (max_comments != -1 and len(comments) >= max_comments):
            break

    return comments[:max_comments] if max_comments != -1 else comments

# ---------- UI ----------

st.title("🎯 YouTube 댓글 수집기 (v2)")

with st.expander("📘 YouTube API Key 발급 방법 안내"):
    st.markdown("""
    1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
    2. 새 프로젝트 생성
    3. `YouTube Data API v3`를 활성화
    4. '사용자 인증 정보' → `API 키 만들기`
    5. 생성된 API 키를 복사하여 아래에 붙여넣으세요.
    """)

# 입력
youtube_url = st.text_input("📺 YouTube 영상 URL 입력", value=SAMPLE_URL)
api_key = st.text_input("🔑 API 키 입력", type="password", value=SAMPLE_API_KEY)

# 댓글 수 설정 (Selectbox + Slider 병행)
st.markdown("### 💬 댓글 수집 개수 선택")
col1, col2 = st.columns(2)

with col1:
    select_count = st.selectbox("빠른 선택", ["100", "500", "1000", "모두"], index=0)

with col2:
    slider_count = st.slider("세부 조절", 100, 1000, step=100, value=100)

# 선택 결과 반영
if select_count == "모두":
    comment_limit = -1  # -1이면 모두
else:
    comment_limit = max(int(select_count), slider_count)

if st.button("댓글 수집 시작"):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.warning("⚠️ 유효한 YouTube URL을 입력해주세요.")
        st.stop()

    with st.spinner("🔄 댓글 수집 중..."):
        comments = get_comments(video_id, api_key, comment_limit)

    if comments:
        st.success(f"✅ 댓글 {len(comments)}개 수집 완료!")
        for i, comment in enumerate(comments, 1):
            st.write(f"💬 {i}. {comment}")
    else:
        st.warning("😥 댓글을 수집할 수 없습니다.")
