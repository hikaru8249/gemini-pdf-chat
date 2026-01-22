import streamlit as st
import os
import tempfile
import base64
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from dotenv import load_dotenv

# 1. 環境設定
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ページ設定（ワイドモード）
st.set_page_config(page_title="多機能 PDF RAG Chat", page_icon="🤖", layout="wide")
st.title("🤖 多機能 PDF RAG Chatbot")

# --- サイドバー設定 ---
st.sidebar.header("⚙️ 設定")

# APIキー入力
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input("Google API Key", type="password")

if not GOOGLE_API_KEY:
    st.warning("APIキーを設定してください。")
    st.stop()

# モデル設定
try:
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

# システムプロンプト設定
st.sidebar.subheader("📝 AIへの指示")
system_prompt = st.sidebar.text_area(
    "AIの役割",
    value="あなたは提供されたPDFの内容に基づいて答えるAIアシスタントです。",
    height=100
)

# --- 関数定義 ---

def display_pdf(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_pdf = base64.b64encode(bytes_data).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

@st.cache_resource(show_spinner=False)
def create_index_from_uploaded_file(uploaded_file):
    with st.spinner("🚀 AIがPDFを読んで学習中..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        documents = SimpleDirectoryReader(input_files=[tmp_path]).load_data()
        index = VectorStoreIndex.from_documents(documents)
        os.remove(tmp_path)
        return index

# --- メイン画面 ---

col1, col2 = st.columns([1, 1])

# チャット履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# ファイルアップロード
with col1:
    uploaded_file = st.file_uploader("PDFをアップロード", type=["pdf"])

if uploaded_file:
    # 右カラム：PDFプレビュー
    with col2:
        st.subheader("📄 PDFプレビュー")
        display_pdf(uploaded_file)

    # 左カラム：チャット処理
    with col1:
        st.subheader("💬 チャット")
        
        # インデックス作成
        try:
            index = create_index_from_uploaded_file(uploaded_file)
            query_engine = index.as_query_engine()

            # 1. 過去のチャット履歴をすべて表示
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # 2. 最新のメッセージが「ユーザー」なら、AIが回答を生成する（ここがポイント）
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    # ★ここでローディング表示（考え中...）
                    with st.spinner("AIが思考中..."):
                        # プロンプトの結合
                        last_user_msg = st.session_state.messages[-1]["content"]
                        final_prompt = f"{system_prompt}\n\n---\nユーザーの質問: {last_user_msg}"
                        
                        # 回答生成
                        response = query_engine.query(final_prompt)
                        st.markdown(response.response)
                
                # 回答を履歴に追加
                st.session_state.messages.append({"role": "assistant", "content": response.response})

            # 3. 入力欄（常に一番下に配置）
            if prompt := st.chat_input("質問を入力してください..."):
                # ユーザーの入力を履歴に追加して、すぐに再読み込み(rerun)する
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")