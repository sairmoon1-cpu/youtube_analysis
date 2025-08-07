import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from collections import Counter
import altair as alt
import re
from datetime import datetime, timedelta

# ✅ 샘플
SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
API_KEY = st.secrets["youtube_api_key"]

# 영상 ID 추출
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 영상 업로드일 수집
def get_video_upload_time(video_id, api_key):
    youtube = build("youtube", "v3", developerKey=api_key)
    response = youtube.videos().list(part="snippet", id=video_id).execute()
    upload_time = response["items"][0]["snippet"]["publishedAt"]
    return pd.to_datetime(upload_time)

# 댓글 수집 (작성 시각 + 좋아요 포함)
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
        pd.to_datetime(timestamps[:max_comments] if max_comments != -1 else timestamps),
        likes[:max_comments] if max_comments != -1 else likes
    )

# ------------------- Streamlit 앱 -------------------

st.title("⏰ YouTube 댓글 시간 분석기")

youtube_url = st.text_input("📺 YouTube 영상 URL", value=SAMPLE_URL)
col1, col2 = st.columns(2)
with col1:
    select_count = st.selectbox("댓글 수 (빠른 선택)", ["100", "500", "1000", "모두"], index=0)
with col2:
    slider_count = st.slider("댓글 수 (세부 조절)", 100, 1000, step=100, value=100)

limit = -1 if select_count == "모두" else max(int(select_count), slider_count)

if st.button("분석 시작"):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.error("⚠️ 유효한 YouTube URL이 아닙니다.")
        st.stop()

    with st.spinner("📥 영상 업로드일 조회 중..."):
        upload_time = get_video_upload_time(video_id, API_KEY)

    with st.spinner("💬 댓글 수집 중..."):
        comments, timestamps, likes = get_comments(video_id, API_KEY, limit)

    if not comments:
        st.warning("댓글을 수집할 수 없습니다.")
        st.stop()

    # DataFrame 구성
    df = pd.DataFrame({
        "댓글 내용": comments,
        "작성 시각": timestamps,
        "좋아요 수": likes
    })
    df["경과 시간 (시)"] = ((df["작성 시각"] - upload_time).dt.total_seconds() // 3600).astype(int)
    df["시간대 (시)"] = df["작성 시각"].dt.hour

    # --------------------- 📈 1. 누적 댓글 수 그래프 ---------------------
    st.subheader("📈 업로드 이후 댓글 누적 수")

    hourly_counts = df.groupby("경과 시간 (시)").size().reset_index(name="댓글 수")
    hourly_counts["누적 댓글 수"] = hourly_counts["댓글 수"].cumsum()

    # 1주일 이내 최대 증가구간 강조
    within_week = hourly_counts[hourly_counts["경과 시간 (시)"] <= 168]
    diffs = within_week["누적 댓글 수"].diff().fillna(0)
    max_idx = diffs.idxmax()
    highlight_hour = within_week.loc[max_idx, "경과 시간 (시)"]

    base_line = alt.Chart(hourly_counts).mark_line().encode(
        x="경과 시간 (시):Q",
        y="누적 댓글 수:Q",
        tooltip=["경과 시간 (시)", "누적 댓글 수"]
    )

    highlight_point = alt.Chart(hourly_counts[hourly_counts["경과 시간 (시)"] == highlight_hour]).mark_point(
        color="red", size=100
    ).encode(
        x="경과 시간 (시):Q",
        y="누적 댓글 수:Q"
    )

    st.altair_chart(base_line + highlight_point, use_container_width=True)

    # ------------------- ⏱ 2. 댓글 작성 시각 vs 좋아요 수 -------------------
    st.subheader("🧭 댓글 작성 시각 vs 좋아요 수")

    st.altair_chart(
        alt.Chart(df).mark_circle(size=60, opacity=0.6).encode(
            x="작성 시각:T",
            y="좋아요 수:Q",
            tooltip=["댓글 내용", "좋아요 수", "작성 시각"]
        ).interactive(),
        use_container_width=True
    )

    # ---------------- 🕰 3. 댓글 시간대별 좋아요 수 합계 ----------------
    st.subheader("🕒 댓글 시간대별 좋아요 수 합계")

    hourly_likes = df.groupby("시간대 (시)")["좋아요 수"].sum().reset_index()

    st.altair_chart(
        alt.Chart(hourly_likes).mark_bar().encode(
            x=alt.X("시간대 (시):O", sort="ascending"),
            y="좋아요 수:Q",
            tooltip=["시간대 (시)", "좋아요 수"]
        ).properties(
            width=600,
            height=400
        ),
        use_container_width=True
    )
