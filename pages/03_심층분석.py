import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from collections import Counter
from soynlp.tokenizer import RegexTokenizer
import re
import altair as alt

# ✅ 샘플
SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
API_KEY = st.secrets["youtube_api_key"]

# 🔍 video ID 추출
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# ✅ 영상 업로드 시각 수집
def get_video_published_time(video_id, api_key):
    youtube = build("youtube", "v3", developerKey=api_key)
    response = youtube.videos().list(part="snippet", id=video_id).execute()
    return response["items"][0]["snippet"]["publishedAt"]

# 💬 댓글 수집 (내용, 시간, 좋아요 수 포함)
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
            likes.append(snippet.get("likeCount", 0))

        next_page_token = response.get("nextPageToken")
        if not next_page_token or (max_comments != -1 and len(comments) >= max_comments):
            break

    return (
        comments[:max_comments] if max_comments != -1 else comments,
        timestamps[:max_comments] if max_comments != -1 else timestamps,
        likes[:max_comments] if max_comments != -1 else likes
    )

# ----------------- Streamlit 앱 ------------------

st.title("📊 YouTube 댓글 시간 & 좋아요 수 분석기")

youtube_url = st.text_input("📺 영상 URL", value=SAMPLE_URL)

col1, col2 = st.columns(2)
with col1:
    select_count = st.selectbox("댓글 개수 (빠른 선택)", ["100", "500", "1000", "모두"], index=0)
with col2:
    slider_count = st.slider("댓글 개수 (세부 조절)", 100, 1000, step=100, value=100)

comment_limit = -1 if select_count == "모두" else max(int(select_count), slider_count)

if st.button("댓글 수집 및 분석 시작"):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.error("❌ 유효한 YouTube URL이 아닙니다.")
        st.stop()

    with st.spinner("📅 영상 업로드 시각 확인 중..."):
        video_published_at = get_video_published_time(video_id, API_KEY)
        video_uploaded_time = pd.to_datetime(video_published_at)

    with st.spinner("💬 댓글 수집 중..."):
        comments, timestamps, likes = get_comments(video_id, API_KEY, comment_limit)

    if not comments:
        st.warning("😥 댓글을 수집하지 못했습니다.")
        st.stop()

    df = pd.DataFrame({
        "댓글 내용": comments,
        "작성 시각": pd.to_datetime(timestamps),
        "좋아요 수": likes
    })

    # 업로드 기준 시간 경과 계산
    df["경과 시간 (분)"] = (df["작성 시각"] - video_uploaded_time).dt.total_seconds() / 60
    df["경과 시간 (시)"] = df["경과 시간 (분)"] / 60
    df["작성 시간대 (시)"] = df["작성 시각"].dt.hour

    st.success(f"✅ 댓글 {len(df)}개 수집 완료! 영상 업로드 시각: {video_uploaded_time}")

    # ---------------- 시각화 ----------------

    st.subheader("📈 영상 업로드 이후 댓글 수 추이")

    df_time = df.copy()
    df_time["경과 시간 (시)"] = df_time["경과 시간 (시)"].round().astype(int)
    hourly_count = df_time.groupby("경과 시간 (시)").size().reset_index(name="댓글 수")

    chart1 = alt.Chart(hourly_count).mark_line(point=True).encode(
        x=alt.X("경과 시간 (시):Q", title="업로드 이후 경과 시간 (시간 단위)"),
        y=alt.Y("댓글 수:Q"),
        tooltip=["경과 시간 (시)", "댓글 수"]
    ).properties(
        title="업로드 후 시간별 댓글 수 추이"
    )

    st.altair_chart(chart1, use_container_width=True)

    st.subheader("🟢 댓글 작성 시각 vs 좋아요 수")

    chart2 = alt.Chart(df).mark_circle(size=60).encode(
        x=alt.X("작성 시각:T", title="댓글 작성 시간"),
        y=alt.Y("좋아요 수:Q"),
        tooltip=["댓글 내용", "좋아요 수", "작성 시각"]
    ).interactive().properties(title="댓글 시간과 좋아요 수 관계")

    st.altair_chart(chart2, use_container_width=True)

    st.subheader("🕒 댓글 시간대별 좋아요 수")

    hourly_likes = df.groupby("작성 시간대 (시)")["좋아요 수"].sum().reset_index()

    chart3 = alt.Chart(hourly_likes).mark_bar().encode(
        x=alt.X("작성 시간대 (시):O", title="댓글 작성 시간대 (24시간)"),
        y=alt.Y("좋아요 수:Q"),
        tooltip=["작성 시간대 (시)", "좋아요 수"]
    ).properties(title="시간대별 좋아요 수 합계")

    st.altair_chart(chart3, use_container_width=True)
