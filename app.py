import streamlit as st
import os
import datetime
import io
from llama_index.core import Settings
from llama_index.core.schema import ImageDocument
from dotenv import load_dotenv

# 分割したモジュールをインポート
# ※ ui.py, logic.py, models.py が同じフォルダにある必要があります
import ui
import logic
from models import get_llm_model, get_embed_model

# 1. 環境設定
load_dotenv()

# ★修正ポイント: 安全なAPIキー取得ロジック
def get_api_key():
    # 1. ユーザー入力 (セッションステート)
    if "user_api_input" in st.session_state and st.session_state.user_api_input:
        return st.session_state.user_api_input
    
    # 2. Streamlit Secrets (クラウド用)
    # ローカルで secrets.toml がない場合のエラーを回避
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            return st.secrets["GOOGLE_API_KEY"]
    except FileNotFoundError:
        pass # ファイルがなければ無視
    except Exception:
        pass # その他のエラーも無視

    # 3. 環境変数 (.env)
    return os.getenv("GOOGLE_API_KEY")

st.set_page_config(page_title="多機能 RAG Chat", page_icon="🤖", layout="wide")
st.title("🤖 多機能 マルチファイル RAG Chatbot")

# CSS適用
ui.load_css("style.css")

# セッション初期化
if "messages" not in st.session_state: st.session_state.messages = []
if "last_source_nodes" not in st.session_state: st.session_state.last_source_nodes = []
if "current_images" not in st.session_state: st.session_state.current_images = []

# --- サイドバー ---
with st.sidebar:
    st.title("🕹️ コントロール")
    st.subheader("1. 資料の追加")
    uploaded_files = st.file_uploader(
        "ファイルをドラッグ", 
        type=["pdf", "docx", "txt", "md", "csv", "xlsx", "png", "jpg", "jpeg"], 
        accept_multiple_files=True
    )
    st.markdown("---")

    with st.expander("⚙️ 設定 (API・モデル)", expanded=False):
        # APIキー入力
        st.text_input(
            "Google API Key", 
            type="password", 
            key="user_api_input",
            help="入力がない場合は環境変数のキーが使用されます"
        )
        
        # モデル選択
        selected_model = st.selectbox(
            "使用モデル",
            ["models/gemini-3-flash-preview"],
            index=0,
            help="Flash: 高速・軽量 / Pro: 高性能"
        )

        st.caption("AIの役割")
        system_prompt = st.text_area("プロンプト", value="あなたは資料に基づき回答するAIです。", height=100)

    # 有効なAPIキーを取得
    active_api_key = get_api_key()
    
    if not active_api_key:
        st.error("👈 APIキーが必要です")
        st.stop()

    try:
        # 選択されたモデルを渡す
        llm = get_llm_model(active_api_key, selected_model)
        embed_model = get_embed_model(active_api_key)
        Settings.llm = llm
        Settings.embed_model = embed_model
    except Exception as e:
        st.error(f"モデルエラー: {e}")
        st.stop()

    st.subheader("2. アクション")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📝", help="要約", use_container_width=True):
            if st.session_state.messages:
                hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                st.session_state.summary_result = llm.complete(f"要約して:\n{hist}").text
    with c2:
        if st.button("🗑️", help="クリア", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_source_nodes = []
            if "summary_result" in st.session_state: del st.session_state.summary_result
            st.rerun()
    with c3:
        chat_log = ""
        for m in st.session_state.messages: chat_log += f"[{m['role']}] {m['content']}\n\n"
        if "summary_result" in st.session_state: chat_log += f"\n--- Summary ---\n{st.session_state.summary_result}"
        st.download_button("💾", data=chat_log, file_name=f"log_{datetime.datetime.now().strftime('%Y%m%d')}.txt", use_container_width=True)
    
    if "summary_result" in st.session_state:
        st.success(st.session_state.summary_result)

# --- メインレイアウト ---
if uploaded_files:
    col1, col2 = st.columns([1, 1])

    # 右カラム：プレビュー (ui.py)
    with col2:
        ui.display_file_preview(uploaded_files)

    # 左カラム：チャット
    with col1:
        st.subheader("💬 チャット")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if st.session_state.last_source_nodes:
            with st.expander("🔍 参照ソースを確認"):
                for node in st.session_state.last_source_nodes:
                    st.info(f"{node.metadata.get('file_name')} (Score: {node.score:.2f})\n{node.text[:100]}...")

    # --- チャット入力欄 ---
    if prompt := st.chat_input("質問を入力してください..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            # logic.py で処理
            index, extracted_images = logic.process_uploaded_files(uploaded_files)
            st.session_state.current_images = extracted_images
            retriever = index.as_retriever(similarity_top_k=5)

            nodes = retriever.retrieve(prompt)
            context_text = "\n\n".join([n.text for n in nodes])
            st.session_state.last_source_nodes = nodes

            final_prompt = (
                f"{system_prompt}\n"
                f"参考資料と画像(あれば)を見て回答してください。\n"
                f"--- 参考資料 ---\n{context_text}\n"
                f"--- ユーザーの質問 ---\n{prompt}"
            )

            image_docs = []
            if st.session_state.current_images:
                for img in st.session_state.current_images:
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='PNG')
                    image_docs.append(ImageDocument(image=img_byte_arr.getvalue()))

            if image_docs:
                response = llm.complete(final_prompt, image_documents=image_docs)
            else:
                response = llm.complete(final_prompt)

            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

else:
    st.info("👈 サイドバーから資料をアップロードしてください")