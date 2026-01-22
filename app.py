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

# ページ設定
st.set_page_config(page_title="多機能 PDF RAG Chat", page_icon="🤖", layout="wide")
st.title("🤖 多機能 PDF RAG Chatbot (Multi-PDF版)")

# --- サイドバー設定 ---
with st.sidebar:
    st.header("⚙️ 設定 & アップロード")

    if not GOOGLE_API_KEY:
        GOOGLE_API_KEY = st.text_input("Google API Key", type="password")

    if not GOOGLE_API_KEY:
        st.warning("APIキーを入力してください")
        st.stop()

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

    st.subheader("📂 PDFアップロード (複数可)")
    # ★変更点1: accept_multiple_files=True にして複数選択を許可
    uploaded_files = st.file_uploader(
        "ここにファイルをドロップ", 
        type=["pdf"], 
        accept_multiple_files=True
    )

    st.subheader("📝 AIへの指示")
    system_prompt = st.text_area(
        "AIの役割",
        value="あなたは提供された複数のPDFの内容に基づいて答えるAIアシスタントです。",
        height=150
    )

    # チャット履歴クリアボタン
    if st.button("🗑️ 会話をクリア"):
        st.session_state.messages = []
        st.session_state.last_source_nodes = []
        st.rerun()

# --- 関数定義 ---

@st.cache_resource(show_spinner=False)
def create_index_from_uploaded_files(uploaded_files):
    with st.spinner(f"🚀 {len(uploaded_files)}つのPDFを学習中..."):
        file_paths = []
        # アップロードされた全ファイルを一時保存
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_paths.append(tmp_file.name)

        # 複数のファイルをまとめて読み込む
        documents = SimpleDirectoryReader(input_files=file_paths).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        # 掃除
        for path in file_paths:
            os.remove(path)
            
        return index

# --- メイン画面 ---

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_source_nodes" not in st.session_state:
    st.session_state.last_source_nodes = []

if uploaded_files:
    col1, col2 = st.columns([1, 1])

    # --- 右カラム：PDFプレビュー (切り替え機能付き) ---
    with col2:
        st.subheader("📄 PDFプレビュー")
        
        # ★変更点2: プレビューするファイルを選択するメニューを作成
        # ファイル名のリストを作成
        file_names = [f.name for f in uploaded_files]
        selected_file_name = st.selectbox("プレビューするファイルを選択:", file_names)
        
        # 選択されたファイルのデータを取得
        selected_file = next(f for f in uploaded_files if f.name == selected_file_name)
        
        # 表示
        pdf_viewer(input=selected_file.getvalue(), height=800)

    # --- 左カラム：チャット ---
    with col1:
        st.subheader("💬 チャット")
        
        try:
            # 複数ファイル対応の関数を呼び出し
            index = create_index_from_uploaded_files(uploaded_files)
            query_engine = index.as_query_engine()

            # 履歴表示
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # AI回答生成
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    with st.spinner("AIが複数の資料から思考中..."):
                        last_user_msg = st.session_state.messages[-1]["content"]
                        final_prompt = f"{system_prompt}\n\n---\nユーザーの質問: {last_user_msg}"
                        
                        response = query_engine.query(final_prompt)
                        st.markdown(response.response)
                        
                        st.session_state.last_source_nodes = response.source_nodes
                    
                    # ソース表示（インデント修正済み）
                    if st.session_state.last_source_nodes:
                        with st.expander("🔍 回答の根拠（ソース）を確認する"):
                            for node in st.session_state.last_source_nodes:
                                # どのファイルの何ページかを表示
                                file_name = node.metadata.get("file_name", "不明")
                                page_label = node.metadata.get("page_label", "不明")
                                score = f"{node.score:.2f}" if node.score else "N/A"
                                
                                st.markdown(f"**📄 {file_name} - P.{page_label} (類似度: {score})**")
                                st.info(node.text[:200] + "...") 
                                st.markdown("---")
                
                st.session_state.messages.append({"role": "assistant", "content": response.response})

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    # 入力欄
    if prompt := st.chat_input("質問を入力してください..."):
        st.session_state.last_source_nodes = []
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

else:
    st.info("👈 左側のサイドバーからPDFファイルをアップロードしてください（複数選択可）。")