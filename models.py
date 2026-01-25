import streamlit as st
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

@st.cache_resource
def get_llm_model(api_key, model_name="models/gemini-3-flash-preview"):
    """回答生成用のLLMモデルを取得 (モデル名指定可能)"""
    return Gemini(
        model=model_name, 
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