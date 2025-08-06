import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from konlpy.tag import Okt
import plotly.express as px
import urllib.request
import os

# --------------------------
# 한글 폰트 웹에서 다운로드
# --------------------------
@st.cache_resource
def download_font():
    font_url = "https://github.com/naver/nanumfont/blob/master/ttf/NanumGothic.ttf?raw=true"
    font_path = "/tmp/NanumGothic.ttf"
    if not os.path.exists(font_path):
        urllib.request.urlretrieve(font_url, font_path)
    return font_path

FONT_PATH = download_font()

# ------------------------
# 유튜브 댓글 수집
# ------------------------
def get_video_id(url):
    import re
    match = re.search(r"(?:v=|youtu.be/)([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None

def get_comments(video_id, max_results=100):
    api_key = st.secrets["youtube_api_key"]
    youtube = build('youtube', 'v3', developerKey=api_key)
    comments = []

    response = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        maxResults=min(max_results, 100),
        textFormat='plainText'
    ).execute()

    for item in response['items']:
        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        comments.append(comment)

    return comments

# ------------------------
# 워드클라우드 생성
# ------------------------
def generate_wordcloud(text_list, font_path):
    text = ' '.join(text_list)
    okt = Okt()
    words = okt.nouns(text)
    word_freq = Counter(words)

    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=400,
        background_color='white'
    ).generate_from_frequencies(word_freq)

    buf = BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode()
    return f"data:image/png;base64,{encoded}"

# ------------------------
# Streamlit App 시작
# ------------------------
st.set_page_config(page_title="YouTube 댓글 키워드 분석기", layout="wide")
st.title("💬 YouTube 댓글 키워드 분석기 (한글 지원)")

url = st.text_input("🎥 분석할 유튜브 영상 URL을 입력하세요")

if st.button("분석 시작") and url:
    video_id = get_video_id(url)
    if not video_id:
        st.error("유효한 유튜브 URL이 아닙니다.")
    else:
        with st.spinner("댓글을 수집하고 분석 중입니다..."):
            comments = get_comments(video_id)
            if not comments:
                st.warning("댓글이 없습니다.")
            else:
                st.success(f"{len(comments)}개의 댓글을 수집했습니다.")
                df = pd.DataFrame({'댓글': comments})

                # 단어 빈도 분석
                all_text = ' '.join(df['댓글'])
                okt = Okt()
                nouns = okt.nouns(all_text)
                word_freq = Counter(nouns)
                top_words = word_freq.most_common(20)
                word_df = pd.DataFrame(top_words, columns=['단어', '빈도'])

                # 시각화
                st.subheader("📊 단어 빈도 Top 20")
                fig = px.bar(word_df, x='단어', y='빈도', title='단어 빈도 막대그래프')
                st.plotly_chart(fig)

                st.subheader("☁️ 워드클라우드")
                img_uri = generate_wordcloud(df['댓글'].tolist(), FONT_PATH)
                st.markdown(f'<img src="{img_uri}" width="100%">', unsafe_allow_html=True)
