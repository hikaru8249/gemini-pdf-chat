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
st.title("🤖 多機能 PDF RAG Chatbot (Streaming版)")

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

    if st.button("🗑️ 会話をクリア"):
        st.session_state.messages = []
        st.session_state.last_source_nodes = []
        st.rerun()

# --- 関数定義 ---

@st.cache_resource(show_spinner=False)
def create_index_from_uploaded_files(uploaded_files):
    with st.spinner(f"🚀 {len(uploaded_files)}つのPDFを学習中..."):
        file_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_paths.append(tmp_file.name)

        documents = SimpleDirectoryReader(input_files=file_paths).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
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

    # --- 右カラム：PDFプレビュー ---
    with col2:
        st.subheader("📄 PDFプレビュー")
        file_names = [f.name for f in uploaded_files]
        selected_file_name = st.selectbox("プレビューするファイルを選択:", file_names)
        selected_file = next(f for f in uploaded_files if f.name == selected_file_name)
        pdf_viewer(input=selected_file.getvalue(), height=800)

    # --- 左カラム：チャット ---
    with col1:
        st.subheader("💬 チャット")
        
        try:
            index = create_index_from_uploaded_files(uploaded_files)
            # ★変更点1: streaming=True を追加して、少しずつ回答を受け取る設定にする
            query_engine = index.as_query_engine(streaming=True)

            # 履歴表示
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # AI回答生成処理
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    # プレースホルダー（空の箱）を作っておく
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # プロンプト作成
                    last_user_msg = st.session_state.messages[-1]["content"]
                    final_prompt = f"{system_prompt}\n\n---\nユーザーの質問: {last_user_msg}"
                    
                    # ストリーミング実行
                    streaming_response = query_engine.query(final_prompt)
                    
                    # ★変更点2: AIから文字が来るたびに画面を更新するループ処理
                    for token in streaming_response.response_gen:
                        full_response += token
                        # カーソル「▌」をつけてタイプライター風に演出
                        response_placeholder.markdown(full_response + "▌")
                    
                    # 最後にカーソルを消して確定表示
                    response_placeholder.markdown(full_response)
                    
                    # ソース情報を保存
                    st.session_state.last_source_nodes = streaming_response.source_nodes
                    
                    # ソース表示
                    if st.session_state.last_source_nodes:
                        with st.expander("🔍 回答の根拠（ソース）を確認する"):
                            for node in st.session_state.last_source_nodes:
                                file_name = node.metadata.get("file_name", "不明")
                                page_label = node.metadata.get("page_label", "不明")
                                score = f"{node.score:.2f}" if node.score else "N/A"
                                
                                st.markdown(f"**📄 {file_name} - P.{page_label} (類似度: {score})**")
                                st.info(node.text[:200] + "...") 
                                st.markdown("---")
                
                # 履歴に追加
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    # 入力欄
    if prompt := st.chat_input("質問を入力してください..."):
        st.session_state.last_source_nodes = []
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

else:
    st.info("👈 左側のサイドバーからPDFファイルをアップロードしてください（複数選択可）。")