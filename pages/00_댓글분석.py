import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re

# 샘플 URL
SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
API_KEY = st.secrets["youtube_api_key"]  # ✅ secrets에서 API 키 불러오기

# video ID 추출
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 댓글 + 시간 + 좋아요 수 수집 함수
def get_comments(video_id, api_key, max_comments=100):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments, timestamps, likes = [], [], []
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
            timestamps.append(snippet["publishedAt"])
            likes.append(snippet.get("likeCount", 0))  # 👍 좋아요 수

        next_page_token = response.get("nextPageToken")
        if not next_page_token or (max_comments != -1 and len(comments) >= max_comments):
            break

    return (
        comments[:max_comments] if max_comments != -1 else comments,
        timestamps[:max_comments] if max_comments != -1 else timestamps,
        likes[:max_comments] if max_comments != -1 else likes
    )

# Streamlit 앱
st.title("📋 YouTube 댓글 분석기 (시간 + 좋아요 수 포함)")

youtube_url = st.text_input("📺 영상 URL", value=SAMPLE_URL)

st.markdown("### 💬 수집할 댓글 개수를 선택해주세요.")
col1, col2 = st.columns(2)
with col1:
    select_count = st.selectbox("빠른 선택", ["100", "500", "1000", "모두"], index=0)
with col2:
    slider_count = st.slider("세부 조절", 100, 1000, step=100, value=100)

if select_count == "모두":
    comment_limit = -1
else:
    comment_limit = max(int(select_count), slider_count)

if st.button("댓글 수집 시작"):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.warning("⚠️ 유효한 YouTube URL을 입력해주세요.")
        st.stop()

    with st.spinner("🔄 댓글 수집 중..."):
        comments, timestamps, likes = get_comments(video_id, API_KEY, comment_limit)

    if comments:
        st.success(f"✅ 댓글 {len(comments)}개 수집 완료!")

        df = pd.DataFrame({
            "댓글 내용": comments,
            "작성 시각": pd.to_datetime(timestamps),
            "좋아요 수": likes
        })

        st.subheader("🗂️ 댓글 목록 (시간 + 좋아요 수 포함)")
        st.dataframe(df.sort_values(by="좋아요 수", ascending=False).reset_index(drop=True))
    else:
        st.warning("😥 댓글이 수집되지 않았습니다.")
