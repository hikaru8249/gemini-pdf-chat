# 🤖 Multi-File RAG Chatbot

Googleの **Gemini 3 flash preview** と **LlamaIndex** を搭載した、実務レベルの多機能AIチャットボットです。
PDFだけでなく、Word、Excel、CSV、画像ファイルなど、あらゆる資料をドラッグ＆ドロップするだけで、AIが内容を理解し、質問に回答します。

## 🚀 デモ
**[👉 アプリを試す (Streamlit Cloud)](https://gemini-pdf-chat-ng5jdhdtphkb3rw2fecb22.streamlit.app/)**
*(※ご自身のデモURLがあれば書き換えてください)*

## ✨ 主な機能 (Features)

### 1. 📂 多彩なファイル形式に対応
以下のファイルを混在させてアップロード可能です。
* **ドキュメント:** PDF, Word (.docx), テキスト (.txt, .md)
* **データ:** Excel (.xlsx), CSV (Shift-JIS/UTF-8 自動判定)
* **画像:** PNG, JPG, JPEG

### 2. 👀 スマート・プレビュー
ファイル形式に応じて最適な方法で中身を表示します。
* **PDF:** 専用ビューワーでページめくり可能。
* **Excel/CSV:** インタラクティブな表（Table）として表示。
* **画像:** そのまま表示。
* **Word:** テキストを抽出して表示。

### 3. 🧠 高精度なRAGエンジン
* **Gemini 3 flash preview:** 高速かつ低コストなLLMを採用。
* **自動文字コード変換:** 日本語のCSV（Shift-JIS）も自動でUTF-8に変換してAIに学習させます。
* **参照スコープ拡大:** CSVなどの短いデータも見逃さないよう、検索範囲（Top-K）を最適化しています。

### 4. 🛠️ 便利なツール群
* **📝 要約:** 長い会話履歴をボタン一つで箇条書き要約。
* **💾 保存:** 会話ログと要約をテキストファイルとしてダウンロード。
* **🔍 ソース提示:** 回答の根拠となった「ファイル名」と「類似度スコア」を表示。

## 📂 プロジェクト構成

保守性を高めるため、機能ごとにファイルを分割しています。

```text
.
├── app.py           # メインアプリ (UIと操作ロジック)
├── models.py        # AIモデル設定 (Gemini, Embeddings)
├── style.css        # デザイン調整用CSS
├── .env             # 環境変数 (APIキー)
└── requirements.txt # 依存ライブラリ一覧
