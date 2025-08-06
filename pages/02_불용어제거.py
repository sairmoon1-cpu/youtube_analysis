import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from collections import Counter
from soynlp.tokenizer import RegexTokenizer
import re
import altair as alt

# ✅ 샘플 URL & API Key
SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
API_KEY = st.secrets["youtube_api_key"]

# 🎯 video ID 추출
def extract_video_id(url):
    pattern = r"(?:v=|youtu\.be/)([\w-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# 💬 댓글 수집
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

# 🚫 한글 + 영어 불용어 리스트
DEFAULT_KO_STOPWORDS = set([
    "영상", "정말", "진짜", "너무", "그리고", "이건", "해서", "하게", "하는", "것", "때문",
    "봤어요", "있어요", "이렇게", "같아요", "이요", "입니다", "그냥", "우리", "이게", "저는", "그거"
])

DEFAULT_EN_STOPWORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "their", "theirs",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "can", "could", "a", "an", "the", "and",
    "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "to",
    "from", "up", "down", "in", "out", "on", "off", "over", "under",
    "again", "further", "then", "once", "here", "there", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just"
])

# 🧠 명사 기반 토큰 추출 + 불용어 제거
@st.cache_data
def extract_meaningful_words(comments):
    tokenizer = RegexTokenizer()
    tokens = []
    for comment in comments:
        tokens += tokenizer.tokenize(comment.lower())  # 소문자화 처리

    # 불용어 제거 (한글/영어 모두)
    tokens = [
        t for t in tokens
        if len(t) > 1 and t not in DEFAULT_KO_STOPWORDS and t not in DEFAULT_EN_STOPWORDS
    ]
    return tokens

# ------------------ Streamlit UI ------------------

st.title("🧠 YouTube 댓글 명사 분석기 (한/영 불용어 제거)")

youtube_url = st.text_input("📺 YouTube 영상 URL", value=SAMPLE_URL)

col1, col2 = st.columns(2)
with col1:
    select_count = st.selectbox("댓글 개수 (빠른 선택)", ["100", "500", "1000", "모두"], index=0)
with col2:
    slider_count = st.slider("댓글 개수 (세부 조절)", 100, 1000, step=100, value=100)

comment_limit = -1 if select_count == "모두" else max(int(select_count), slider_count)

if st.button("분석 시작"):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        st.error("⚠️ 유효한 YouTube URL이 아닙니다.")
        st.stop()

    with st.spinner("🔄 댓글 수집 중..."):
        comments = get_comments(video_id, API_KEY, comment_limit)

    if not comments:
        st.warning("댓글을 수집하지 못했습니다.")
        st.stop()

    with st.spinner("🧠 명사 추출 및 불용어 제거 중..."):
        clean_tokens = extract_meaningful_words(comments)
        freq = Counter(clean_tokens)
        df_freq = pd.DataFrame(freq.items(), columns=["단어", "빈도수"]).sort_values(by="빈도수", ascending=False)

    st.subheader("📊 상위 20개 단어 (불용어 제거 후)")

    # st 기본 bar_chart
    st.bar_chart(df_freq.head(20).set_index("단어"))

    # Altair 차트
    st.altair_chart(
        alt.Chart(df_freq.head(20)).mark_bar().encode(
            x=alt.X("단어:N", sort="-y"),
            y="빈도수:Q",
            tooltip=["단어", "빈도수"]
        ).properties(
            width=600,
            height=400,
            title="상위 20개 단어 (Altair 시각화)"
        )
    )
