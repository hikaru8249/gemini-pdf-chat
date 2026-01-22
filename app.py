import streamlit as st
import os
import tempfile
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer

# 1. 環境設定
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ページ設定（ワイドモード必須）
st.set_page_config(page_title="多機能 PDF RAG Chat", page_icon="🤖", layout="wide")
st.title("🤖 多機能 PDF RAG Chatbot")

# --- サイドバー設定 (アップロード機能) ---
with st.sidebar:
    st.header("⚙️ 設定 & アップロード")

    # APIキー入力
    if not GOOGLE_API_KEY:
        GOOGLE_API_KEY = st.text_input("Google API Key", type="password")

    if not GOOGLE_API_KEY:
        st.warning("APIキーを入力してください")
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

    # ファイルアップロード
    st.subheader("📂 PDFアップロード")
    uploaded_file = st.file_uploader("ここにファイルをドロップ", type=["pdf"])

    # システムプロンプト設定
    st.subheader("📝 AIへの指示")
    system_prompt = st.text_area(
        "AIの役割",
        value="あなたは提供されたPDFの内容に基づいて答えるAIアシスタントです。",
        height=150
    )

# --- 関数定義 ---

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

# チャット履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

if uploaded_file:
    # ★ここが変更点: 画面を左右に分割 (左:チャット, 右:PDF)
    col1, col2 = st.columns([1, 1]) # 1:1の比率で分割

    # --- 右カラム (PDFプレビュー) ---
    with col2:
        st.subheader("📄 PDFプレビュー")
        # 高さを指定してスクロールしやすくする
        pdf_viewer(input=uploaded_file.getvalue(), height=800)

    # --- 左カラム (チャット) ---
    with col1:
        st.subheader("💬 チャット")
        
        try:
            index = create_index_from_uploaded_file(uploaded_file)
            query_engine = index.as_query_engine()

            # 履歴表示 (左側のカラム内だけに表示)
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # AI回答生成ロジック
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner("AIが思考中..."):
                        last_user_msg = st.session_state.messages[-1]["content"]
                        final_prompt = f"{system_prompt}\n\n---\nユーザーの質問: {last_user_msg}"
                        
                        response = query_engine.query(final_prompt)
                        st.markdown(response.response)
                
                st.session_state.messages.append({"role": "assistant", "content": response.response})

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    # 入力欄 (st.chat_inputは自動的に画面最下部に固定されます)
    if prompt := st.chat_input("質問を入力してください..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

else:
    st.info("👈 左側のサイドバーからPDFファイルをアップロードしてください。")