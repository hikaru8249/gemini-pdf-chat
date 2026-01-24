import streamlit as st
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# モデル設定をここに集約
# st.cache_resource を使うことで、メイン側で何回呼ばれても再生成を防ぎます

@st.cache_resource
def get_llm_model(api_key):
    """回答生成用のLLMモデルを取得"""
    return Gemini(
        model="models/gemini-3-flash-preview", 
        api_key=api_key, 
        temperature=0.3
    )

@st.cache_resource
def get_embed_model(api_key):
    """ベクトル化用の埋め込みモデルを取得"""
    return GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=api_key
    )