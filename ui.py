# ui.py
import streamlit as st
import os
import tempfile
import pandas as pd
import docx2txt
from streamlit_pdf_viewer import pdf_viewer
from logic import extract_images_from_excel # 画像抽出ロジックを利用

def load_css(file_name):
    """CSSファイルを読み込む"""
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass
    except Exception:
        pass

def display_file_preview(uploaded_files):
    """右カラムのファイルプレビュー領域を描画"""
    st.subheader("📄 資料プレビュー")
    file_names = [f.name for f in uploaded_files]
    
    if not file_names:
        return

    s_name = st.selectbox("ファイル選択:", file_names)
    s_file = next(f for f in uploaded_files if f.name == s_name)
    s_file.seek(0)
    ext = os.path.splitext(s_file.name)[1].lower()

    try:
        if ext == ".pdf":
            pdf_viewer(input=s_file.getvalue(), height=800)
        
        elif ext == ".xlsx":
            st.dataframe(pd.read_excel(s_file), height=300)
            s_file.seek(0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(s_file.getvalue())
                imgs = extract_images_from_excel(tmp.name)
                if imgs:
                    st.info(f"📸 画像 {len(imgs)} 枚を検出")
                    cols = st.columns(min(3, len(imgs)))
                    for i, img in enumerate(imgs):
                        with cols[i % 3]:
                            st.image(img, use_container_width=True)
                os.remove(tmp.name)

        elif ext in [".png", ".jpg", ".jpeg"]:
            st.image(s_file)
        
        elif ext == ".csv":
            try:
                df = pd.read_csv(s_file)
            except UnicodeDecodeError:
                s_file.seek(0)
                df = pd.read_csv(s_file, encoding='shift_jis')
            st.dataframe(df, height=400)
            
        elif ext == ".docx":
            st.text_area("内容", docx2txt.process(s_file), height=600)
        else:
            st.text(s_file.getvalue().decode("utf-8", "ignore"))
            
    except Exception as e:
        st.error(f"プレビューエラー: {e}")