import os
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

# LlamaIndexの主要コンポーネント
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# 環境変数の読み込み
load_dotenv()

# 1. APIキーの設定
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("APIキーが見つかりません")
    st.stop()

# 2. LlamaIndexの設定（ここがプロの技！）
# LLM（回答する頭脳）にGeminiを指定
Settings.llm = Gemini(
    model="gemini-3-flash-preview", 
    api_key=api_key, 
    temperature=0.3
)
# Embedding（検索用に文章を数値化する機能）にもGeminiを指定
Settings.embed_model = GeminiEmbedding(
    model_name="models/text-embedding-004", 
    api_key=api_key
)

st.title("🔍 Pro RAG Chatbot (LlamaIndex)")

# --- サイドバー: PDFアップロード ---
with st.sidebar:
    st.header("ドキュメント登録")
    uploaded_file = st.file_uploader("PDFをアップロード", type=["pdf"])
    
    # セッション（メモリ）にインデックスがあるか確認
    if "index" not in st.session_state:
        st.session_state.index = None

    if uploaded_file is not None and st.session_state.index is None:
        with st.spinner("AI用検索インデックスを作成中..."):
            try:
                # PDFからテキスト抽出
                reader = PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                
                # LlamaIndex用の「Document」形式に変換
                documents = [Document(text=text)]
                
                # ★ここが核心！ベクトルインデックスの作成
                # テキストを自動で分割し、数値化して検索できるようにする
                index = VectorStoreIndex.from_documents(documents)
                
                # セッションに保存
                st.session_state.index = index
                st.success("インデックス作成完了！検索可能です。")
                
            except Exception as e:
                st.error(f"エラー: {e}")

# --- チャット画面 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# 履歴表示
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("質問を入力してください"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # AIの回答生成
    with st.chat_message("assistant"):
        if st.session_state.index is None:
            response_text = "まずはサイドバーからPDFをアップロードしてください。"
            st.warning(response_text)
        else:
            try:
                # インデックスを使って「検索エンジン」を作る
                query_engine = st.session_state.index.as_query_engine()
                
                # 検索 ＋ 回答生成
                response = query_engine.query(prompt)
                response_text = str(response)
                
                st.markdown(response_text)
            except Exception as e:
                response_text = f"エラーが発生しました: {e}"
                st.error(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})