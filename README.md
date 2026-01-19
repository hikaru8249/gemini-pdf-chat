# 📄 PDF AI Chatbot powered by Google Gemini

PDFドキュメントをアップロードし、その内容についてAI（Google Gemini）と対話できるチャットボットアプリケーションです。
RAG（Retrieval-Augmented Generation）技術を活用し、ドキュメントに基づいた正確な回答を生成します。

## 🚀 デモ
[https://gemini-pdf-chat-ng5jdhdtphkb3rw2fecb22.streamlit.app/]

## ✨ 機能
- **PDF読み込み**: ドラッグ＆ドロップで簡単にPDFをアップロード
- **AI対話**: Google Gemini 1.5 Flash (最新モデル) を使用した高速レスポンス
- **コンテキスト理解**: ドキュメント全体の内容を考慮した回答生成
- **ストリーミング表示**: リアルタイムで回答を表示する優れたUX

## 🛠 使用技術
- **言語**: Python 3.10+
- **フレームワーク**: Streamlit
- **AIモデル**: Google Gemini API (gemini-1.5-flash / gemini-3-flash-preview)
- **ライブラリ**:
  - `google-generativeai`: LLM連携
  - `pypdf`: PDFテキスト抽出
  - `python-dotenv`: 環境変数管理

## 📦 ローカルでの実行方法

1. リポジトリをクローン
```bash
git clone [あなたのリポジトリのURL]
cd [フォルダ名]
