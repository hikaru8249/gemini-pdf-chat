# 🤖 Advanced Multi-PDF RAG Chatbot

Googleの **Gemini 3 flash preview** と **LlamaIndex** を駆使した、実務レベルのPDF対話型AIチャットボットです。
複数のPDFを同時に読み込み、それらを横断して検索・回答することができます。また、ChatGPTのような**リアルタイム・ストリーミング表示**に対応し、快適なユーザー体験を提供します。

## 🚀 デモ
**[👉 アプリを試す (Streamlit Cloud)](https://gemini-pdf-chat-ng5jdhdtphkb3rw2fecb22.streamlit.app/)**

## ✨ 主な機能 (Features)

### 1. 📂 複数PDFの横断検索 (Multi-PDF Support)
* 複数のPDFファイル（マニュアル、契約書、議事録など）を一度にアップロード可能。
* AIが全ての資料を横断的に検索し、**「Aの資料とBの資料を比較して」** といった質問にも回答します。

### 2. ⚡ リアルタイム・ストリーミング (Streaming Response)
* AIの思考・生成プロセスを可視化。
* ChatGPTのように文字がパラパラと表示されるタイプライター演出により、体感待ち時間を大幅に短縮。

### 3. 🔍 根拠の提示 (Source Citation)
* AIが回答に使用した「具体的な情報源」を表示。
* **「どのファイルの、何ページの、どの文章か」** を類似度スコア付きで確認できるため、ハルシネーション（嘘）を抑制できます。

### 4. 👀 インタラクティブなプレビュー
* チャット画面の横でPDFの中身を閲覧可能。
* アップロードした複数のファイルから、見たいものをプルダウンで切り替えて表示できます。

### 5. ⚙️ 高速化 & カスタマイズ
* `Streamlit Caching` により、2回目以降の質問はインデックス再作成なしで即座に回答。
* サイドバーから「AIの役割（システムプロンプト）」を自由に変更可能。

## 🛠 使用技術 (Tech Stack)

* **Frontend:** [Streamlit](https://streamlit.io/)
* **LLM:** Google Gemini 3 flash preview (高速・低コスト)
* **Embeddings:** Google Gemini Text Embedding 004
* **RAG Framework:** [LlamaIndex](https://www.llamaindex.ai/)
* **PDF Viewer:** `streamlit-pdf-viewer`

## 📦 ローカルでの実行方法

1. **リポジトリをクローン**
   ```bash
   git clone [あなたのリポジトリのURL]
   cd [フォルダ名]
