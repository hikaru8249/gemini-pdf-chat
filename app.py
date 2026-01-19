import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from pypdf import PdfReader

# 環境変数の読み込み
load_dotenv()

# APIキー設定
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("APIキーが見つかりません")
    st.stop()

genai.configure(api_key=api_key)
# ★ここで成功したモデル名を指定
model = genai.GenerativeModel("gemini-3-flash-preview")

st.title("📄 PDF AI Chatbot (Gemini 3)")

# --- サイドバー: PDFアップロード機能 ---
with st.sidebar:
    st.header("ドキュメントアップロード")
    uploaded_file = st.file_uploader("PDFファイルをドラッグ＆ドロップ", type=["pdf"])
    
    document_text = ""
    if uploaded_file is not None:
        try:
            # PDFからテキストを抽出
            reader = PdfReader(uploaded_file)
            for page in reader.pages:
                document_text += page.extract_text()
            st.success(f"読み込み完了: {len(document_text)}文字")
        except Exception as e:
            st.error(f"読み込みエラー: {e}")

# --- メインチャット画面 ---

# 履歴の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話を表示
for message in st.session_state.messages:
    role_show = "assistant" if message["role"] == "model" else "user"
    with st.chat_message(role_show):
        st.markdown(message["content"])

# ユーザー入力
if prompt := st.chat_input("このPDFについて質問してね"):
    # ユーザー入力を表示
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Geminiへの指示（プロンプト）を作成
    # ここがポイント: PDFの中身をプロンプトに埋め込みます
    if document_text:
        full_prompt = f"""
以下の「参考ドキュメント」の内容に基づいて、ユーザーの質問に答えてください。

[参考ドキュメント]
{document_text}

[ユーザーの質問]
{prompt}
"""
    else:
        # PDFがない場合は普通のチャット
        full_prompt = prompt

    # APIへの送信履歴を作成（直近のやり取りのみ送信する簡易版）
    gemini_history = []
    # 直前の会話があれば文脈として追加（メモリ節約のため最新2往復程度推奨だが、今回はシンプルに）
    # 今回は「一問一答」形式でPDFの内容を聞くため、historyを使わず直接 generate_content を叩きます

    with st.chat_message("assistant"):
        try:
            # stream=True で文字がパラパラ出るようにする
            response_stream = model.generate_content(full_prompt, stream=True)
            
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in response_stream:
                if chunk.text:
                    full_response += chunk.text
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # 履歴に保存
            st.session_state.messages.append({"role": "model", "content": full_response})

        except Exception as e:
            st.error(f"エラー: {e}")