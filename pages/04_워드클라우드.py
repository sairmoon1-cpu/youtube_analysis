import streamlit as st
import pandas as pd
import requests
import io, os, tempfile, urllib.request
import matplotlib.pyplot as plt
from matplotlib import font_manager
from wordcloud import WordCloud
from collections import Counter
from googleapiclient.discovery import build
import re

# 🔧 폰트 설정 함수
@st.cache_resource
def get_font_path():
    """나눔고딕 폰트 파일을 다운로드하고 경로를 반환합니다."""
    url = "https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    tmp_path = os.path.join(tempfile.gettempdir(), "NanumGothic.ttf")
    if not os.path.exists(tmp_path):
        try:
            urllib.request.urlretrieve(url, tmp_path)
        except urllib.error.URLError as e:
            st.error(f"폰트 파일을 다운로드하는 중 오류가 발생했습니다: {e}")
            return None
    return tmp_path

# 폰트 경로를 가져오고 Matplotlib에 설정합니다.
FONT_PATH = get_font_path()
if FONT_PATH:
    plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT_PATH).get_name()
else:
    st.error("폰트를 불러올 수 없어 워드클라우드 생성이 불가능합니다.")


# 📦 댓글 및 영상 제목 수집 함수
def get_video_data(youtube_url, max_comments):
    """YouTube API를 사용하여 댓글과 영상 제목을 수집합니다."""
    try:
        video_id = youtube_url.split("v=")[-1].split("&")[0]
        api_key = st.secrets["youtube_api_key"]
        youtube = build("youtube", "v3", developerKey=api_key)
        
        # 영상 제목 가져오기
        video_title = ""
        try:
            video_response = youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            video_title = video_response['items'][0]['snippet']['title']
        except Exception as e:
            st.warning(f"영상 제목을 가져오는 데 실패했습니다: {e}")
            video_title = "Untitled"


        # 댓글 가져오기
        comments = []
        next_page_token = None
        while len(comments) < max_comments:
            request_count = min(100, max_comments - len(comments))
            if request_count <= 0:
                break

            response = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=request_count,
                pageToken=next_page_token,
                order="relevance",
                textFormat="plainText"
            ).execute()

            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        
        return comments, video_title

    except Exception as e:
        st.error(f"데이터 수집 중 오류가 발생했습니다: {e}")
        st.info("올바른 YouTube 영상 URL인지, API 키가 유효한지 확인해주세요.")
        return [], None

# 🧼 텍스트 전처리
def clean_text(text):
    """특수문자, 이모티콘 등을 제거하여 텍스트를 정제합니다."""
    cleaned_text = re.sub(r"[^\uAC00-\uD7A3a-zA-Z0-9\s]", "", text)
    return cleaned_text.strip()

def tokenize(texts, stopwords):
    """텍스트 리스트에서 불용어를 제외하고 2글자 이상의 한글/영어 단어만 추출하여 토큰화합니다."""
    token_list = []
    for line in texts:
        tokens = re.findall(r"[a-zA-Z가-힣]{2,}", line.lower())
        filtered_tokens = [word for word in tokens if word not in stopwords]
        token_list.extend(filtered_tokens)
    return token_list

# 🌥️ 워드클라우드 생성 함수
def generate_wordcloud(tokens, dpi=200, max_words=100):
    """단어 토큰을 기반으로 워드클라우드 Figure 객체를 생성하여 반환합니다."""
    if not FONT_PATH:
        st.error("폰트 파일이 없어 워드클라우드를 생성할 수 없습니다.")
        return None

    word_freq = Counter(tokens).most_common(max_words)
    
    wc = WordCloud(
        font_path=FONT_PATH,
        background_color="white",
        width=800,
        height=600,
        max_words=max_words
    ).generate_from_frequencies(dict(word_freq))

    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=dpi)
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    return fig

# ────────────────────── Streamlit UI ──────────────────────
st.set_page_config("YouTube 댓글 워드클라우드", "☁️", layout="wide")
st.title("☁️ YouTube 댓글 워드클라우드 생성기")
st.markdown("YouTube 영상의 댓글을 분석하여 핵심 단어를 보여주는 워드클라우드를 만들어보세요!")

SAMPLE_URL = "https://www.youtube.com/watch?v=WXuK6gekU1Y"
youtube_url = st.text_input("🎥 YouTube 영상 URL", value=SAMPLE_URL)

with st.expander("🚫 불용어 설정 (클릭하여 수정)"):
    default_stopwords = "ㅋㅋ,ㅎㅎ,ㅠㅠ,이,그,저,것,수,등,좀,잘,더,진짜,너무,완전,정말,근데,그래서,그리고,하지만,이제,영상,구독,좋아요,the,a,an,is,are,be,to,of,and,in,that,it,with,for,on,this,i,you,he,she,we,they,my,your,lol,omg,btw"
    user_stopwords = st.text_area(
        "제외할 단어 (쉼표로 구분)",
        value=default_stopwords,
        height=100,
        help="분석에서 제외하고 싶은 단어를 쉼표(,)로 구분하여 입력하세요."
    )

col1, col2 = st.columns(2)
with col1:
    max_comments = st.slider("💬 분석할 최대 댓글 수", min_value=100, max_value=2000, step=100, value=500)
with col2:
    max_words = st.slider("🔠 워드클라우드에 표시할 단어 수", min_value=20, max_value=200, step=10, value=100)

if st.button("🚀 워드클라우드 생성"):
    if not youtube_url:
        st.warning("YouTube 링크를 입력해주세요.")
    elif not FONT_PATH:
        st.error("폰트 파일을 불러올 수 없어 앱을 실행할 수 없습니다.")
    else:
        stopword_list = [word.strip() for word in user_stopwords.lower().split(',') if word.strip()]
        
        with st.spinner("YouTube 댓글과 영상 정보를 수집하고 있습니다..."):
            comments, video_title = get_video_data(youtube_url, max_comments)

        if not comments:
            st.error("댓글을 가져오지 못했습니다. 영상 ID, 댓글 공개 여부 또는 API 키 설정을 확인해주세요.")
        else:
            st.success(f"✅ '{video_title}' 영상의 댓글 {len(comments)}개를 성공적으로 수집했습니다!")

            with st.spinner("텍스트를 전처리하고 단어를 분석 중입니다..."):
                cleaned = [clean_text(c) for c in comments]
                tokens = tokenize(cleaned, stopword_list)

            if not tokens:
                st.warning("분석할 수 있는 유효한 단어(2글자 이상 한글/영어)가 댓글에 충분하지 않습니다.")
            else:
                st.info(f"분석된 유효 단어 수: {len(tokens)}개")
                with st.spinner("☁️ 워드클라우드를 생성하고 있습니다..."):
                    wordcloud_fig = generate_wordcloud(tokens, dpi=200, max_words=max_words)
                    
                    if wordcloud_fig:
                        st.pyplot(wordcloud_fig)
                        
                        # 이미지 다운로드 기능 추가
                        buf = io.BytesIO()
                        wordcloud_fig.savefig(buf, format="png", bbox_inches='tight')
                        
                        # 파일명으로 사용할 수 없는 문자 제거
                        clean_title = re.sub(r'[\\/*?:"<>|]', "", video_title)
                        file_name = f"{clean_title}_워드클라우드.png"
                        
                        st.download_button(
                            label="🖼️ 이미지 다운로드",
                            data=buf.getvalue(),
                            file_name=file_name,
                            mime="image/png"
                        )
