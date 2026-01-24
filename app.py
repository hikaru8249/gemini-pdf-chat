import streamlit as st
import os
import tempfile
import datetime
import pandas as pd
import docx2txt
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer
import openpyxl

# ★変更点: 作成した models.py から関数をインポート
from models import get_llm_model, get_embed_model

# 1. 環境設定
load_dotenv()
env_api_key = os.getenv("GOOGLE_API_KEY")

# ページ設定
st.set_page_config(page_title="多機能 RAG Chat", page_icon="🤖", layout="wide")

st.title("🤖 多機能 マルチファイル RAG Chatbot")

# --- 関数定義: CSS読み込み ---
def load_css(file_name):
    # Windows対応: utf-8指定
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

try:
    load_css("style.css")
except FileNotFoundError:
    st.warning("⚠️ style.css が見つかりません。")

# --- 関数定義: インデックス作成 ---
@st.cache_resource(show_spinner=False)
def create_index_from_uploaded_files(uploaded_files):
    with st.spinner(f"🚀 {len(uploaded_files)}つのファイルを学習中..."):
        file_paths = []
        for uploaded_file in uploaded_files:
            uploaded_file.seek(0)
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                # CSV文字コード対策
                if file_ext == ".csv":
                    try:
                        df = pd.read_csv(uploaded_file)
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding='shift_jis')
                    
                    # UTF-8 で保存し直す
                    df.to_csv(tmp_file.name, index=False, encoding='utf-8')
                    file_paths.append(tmp_file.name)
                
                else:
                    tmp_file.write(uploaded_file.getvalue())
                    file_paths.append(tmp_file.name)

        # LlamaIndexで読み込み
        documents = SimpleDirectoryReader(input_files=file_paths).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        for path in file_paths:
            os.remove(path)
            
        return index

# --- セッションステート初期化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_source_nodes" not in st.session_state:
    st.session_state.last_source_nodes = []

# --- サイドバー設定 ---
with st.sidebar:
    st.title("🕹️ コントロール")
    
    st.subheader("1. 資料の追加")
    uploaded_files = st.file_uploader(
        "ファイルをドラッグ", 
        type=["pdf", "docx", "txt", "md", "csv", "xlsx", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    
    st.markdown("---")

    with st.expander("⚙️ 設定 (API Key)", expanded=False):
        user_input_key = st.text_input("API Key", type="password", key="user_api_input")
        st.caption("AIの役割")
        system_prompt = st.text_area(
            "プロンプト",
            value="あなたは提供された資料の内容に基づいて答えるAIアシスタントです。",
            height=100
        )

    active_api_key = user_input_key if user_input_key else env_api_key

    if not active_api_key:
        st.error("👈 APIキーを設定してください")
        st.stop()

    # --- モデル設定 (models.py から読み込み) ---
    try:
        # models.py で定義した関数を使用
        llm = get_llm_model(active_api_key)
        embed_model = get_embed_model(active_api_key)
        
        Settings.llm = llm
        Settings.embed_model = embed_model
    except Exception as e:
        st.error(f"モデル設定エラー: {e}")
        st.stop()

    st.subheader("2. アクション")
    col_btn1, col_btn2, col_btn3 = st.columns(3)

    with col_btn1:
        if st.button("📝", help="会話履歴を要約", use_container_width=True):
            if not st.session_state.messages:
                st.warning("履歴なし")
            else:
                with st.spinner("要約中..."):
                    chat_history = "\n".join([f"{'ユーザー' if m['role']=='user' else 'AI'}: {m['content']}" for m in st.session_state.messages])
                    summary_prompt = f"以下の会話を箇条書きで要約して:\n\n{chat_history}"
                    try:
                        response = llm.complete(summary_prompt)
                        st.session_state.summary_result = response.text
                    except Exception as e:
                        st.error(f"エラー: {e}")

    with col_btn2:
        if st.button("🗑️", help="クリア", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_source_nodes = []
            if "summary_result" in st.session_state:
                del st.session_state.summary_result
            st.rerun()
            
    with col_btn3:
        chat_log_str = ""
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "AI"
            chat_log_str += f"[{role}] {msg['content']}\n\n"
        
        if "summary_result" in st.session_state:
            chat_log_str += f"\n--- 要約 ---\n{st.session_state.summary_result}\n"

        now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            label="💾", help="保存",
            data=chat_log_str,
            file_name=f"chat_log_{now}.txt",
            mime="text/plain",
            use_container_width=True
        )

    if "summary_result" in st.session_state:
        st.success(f"**💡 要約:**\n\n{st.session_state.summary_result}")

# --- メイン画面 ---

if uploaded_files:
    col1, col2 = st.columns([1, 1])

    # --- プレビュー ---
    with col2:
        st.subheader("📄 資料プレビュー")
        file_names = [f.name for f in uploaded_files]
        if file_names:
            selected_file_name = st.selectbox("表示するファイル:", file_names)
            selected_file = next(f for f in uploaded_files if f.name == selected_file_name)
            selected_file.seek(0)
            
            file_ext = os.path.splitext(selected_file.name)[1].lower()
            try:
                if file_ext == ".pdf":
                    pdf_viewer(input=selected_file.getvalue(), height=800)
                elif file_ext == ".csv":
                    try:
                        df = pd.read_csv(selected_file)
                    except UnicodeDecodeError:
                        selected_file.seek(0)
                        df = pd.read_csv(selected_file, encoding='shift_jis')
                    st.dataframe(df, height=400)
                elif file_ext == ".xlsx":
                    df = pd.read_excel(selected_file)
                    st.dataframe(df, height=400)
                elif file_ext in [".png", ".jpg", ".jpeg"]:
                    st.image(selected_file, caption=selected_file_name, use_container_width=True)
                elif file_ext == ".docx":
                    text = docx2txt.process(selected_file)
                    st.info("ℹ️ Wordテキスト表示")
                    st.text_area("内容", text, height=600)
                elif file_ext in [".txt", ".md"]:
                    string_data = selected_file.getvalue().decode("utf-8", errors="ignore")
                    st.text_area("内容", string_data, height=600)
                else:
                    st.warning(f"{file_ext} はプレビュー非対応")
            except Exception as e:
                st.error(f"プレビューエラー: {e}")

    # --- チャット ---
    with col1:
        st.subheader("💬 チャット")
        try:
            index = create_index_from_uploaded_files(uploaded_files)
            
            # CSVなど短いデータ用に similarity_top_k を多めに設定
            query_engine = index.as_query_engine(
                streaming=True,
                similarity_top_k=5
            )

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    last_user_msg = st.session_state.messages[-1]["content"]
                    final_prompt = f"{system_prompt}\n\n---\nユーザーの質問: {last_user_msg}"
                    
                    streaming_response = query_engine.query(final_prompt)
                    
                    for token in streaming_response.response_gen:
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    st.session_state.last_source_nodes = streaming_response.source_nodes
                    
                    if st.session_state.last_source_nodes:
                        with st.expander("🔍 根拠（ソース）"):
                            for node in st.session_state.last_source_nodes:
                                file_name = node.metadata.get("file_name", "不明")
                                page = node.metadata.get("page_label", "-")
                                score = f"{node.score:.2f}" if node.score else "N/A"
                                st.markdown(f"**{file_name} - Score: {score}**")
                                st.info(node.text[:100] + "...")
                                st.markdown("---")
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"処理エラー: {e}")

    if prompt := st.chat_input("質問を入力..."):
        st.session_state.last_source_nodes = []
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

else:
    st.info("👈 サイドバーから資料をアップロードしてください。")