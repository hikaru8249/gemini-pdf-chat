# 📄 High-Performance PDF RAG Chatbot

Googleの最新AIモデル **Gemini 3 Flash Preview** と、データフレームワーク **LlamaIndex** を組み合わせた、高速で多機能なPDF対話型AIチャットボットです。
ユーザーがアップロードしたPDFの内容をAIがベクトル検索（RAG）し、その内容に基づいて正確かつ高速に回答します。

## 🚀 デモ
**[👉 アプリを試す (Streamlit Cloud)](https://gemini-pdf-chat-ng5jdhdtphkb3rw2fecb22.streamlit.app/)**

## ✨ 主な機能
* **⚡ 爆速レスポンス**: Streamlitのキャッシュ機能とGeminiの高速モデルを組み合わせ、2回目以降の質問は待ち時間ゼロで回答。
* **📚 本格的RAG (検索拡張生成)**: `LlamaIndex` を採用。PDFをベクトル化して検索するため、長文ドキュメントでも高精度な回答が可能。
* **👀 PDFプレビュー**: アップロードした資料をサイドバーで閲覧しながらチャットが可能（`streamlit-pdf-viewer` 採用）。
* **⚙️ カスタム設定**: AIへの「役割（プロンプト）」やAPIキーを画面上で自由に設定可能。

## 🛠 使用技術
* **言語**: Python 3.10+
* **フレームワーク**: Streamlit
* **AIモデル**: Google Gemini 3 Flash Preview
* **Embeddings**: Gemini Text Embedding 004
* **オーケストレーション**: `llama-index` (RAG構築)
* **UIコンポーネント**: `streamlit-pdf-viewer`

## 📦 ローカルでの実行方法

1. **リポジトリをクローン**
   ```bash
   git clone [あなたのリポジトリのURL]
   cd [フォルダ名]
