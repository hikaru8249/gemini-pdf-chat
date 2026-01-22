import streamlit as st
import os
import tempfile
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from dotenv import load_dotenv

# 1. 環境設定
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ページ設定
st.set_page_config(page_title="爆速 PDF RAG Chat", page_icon="🚀")
st.title("🚀 爆速 PDF RAG Chatbot")

# サイドバーにAPIキー入力欄（念のため）
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input("Google API Key", type="password")

if not GOOGLE_API_KEY:
    st.warning("設定ファイル(.env)が見つからないか、APIキーがありません。サイドバーに入力してください。")
    st.stop()

# 2. モデル設定 (ここでGeminiを指名)
try:
    # 以前動いた設定（gemini-1.5-flash または gemini-pro）を使ってください
    Settings.llm = Gemini(
        model="models/gemini-3-flash-preview", 
        api_key=GOOGLE_API_KEY, 
        temperature=0.3
    )
    Settings.embed_model = GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=GOOGLE_API_KEY
    )
except Exception as e:
    st.error(f"モデル設定エラー: {e}")
    st.stop()

# --- 🚀 ここが爆速化のポイント！ ---
# @st.cache_resource をつけると、この関数の結果がメモリに保存されます。
# 同じファイルがアップロードされている限り、2回目以降は「一瞬」で終わります。
@st.cache_resource(show_spinner=False)
def create_index_from_uploaded_file(uploaded_file):
    with st.spinner("🚀 AIがPDFを読んで学習中...（これには少し時間がかかります）"):
        # 一時ファイルとして保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # データを読み込んでインデックス作成
        documents = SimpleDirectoryReader(input_files=[tmp_path]).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        # 掃除（一時ファイルを削除）
        os.remove(tmp_path)
        return index

# 3. ファイルアップロードとチャット画面
uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type=["pdf"])

if uploaded_file:
    # ここでキャッシュ機能付きの関数を呼び出す
    try:
        index = create_index_from_uploaded_file(uploaded_file)
        query_engine = index.as_query_engine()
        st.success("✅ 準備完了！質問してください。")

        # チャット履歴の初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 履歴を表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # ユーザーの入力処理
        if prompt := st.chat_input("このPDFについて聞いてみて..."):
            # ユーザーの質問を表示
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # AIの回答生成
            with st.chat_message("assistant"):
                response = query_engine.query(prompt)
                st.markdown(response.response)
            st.session_state.messages.append({"role": "assistant", "content": response.response})

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")