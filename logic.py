# logic.py
import os
import tempfile
import io
import pandas as pd
from PIL import Image
import openpyxl
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
import streamlit as st

def extract_images_from_excel(file_path):
    """Excelファイルから画像を抽出してPIL Imageリストとして返す"""
    images = []
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        for sheet in wb.worksheets:
            if hasattr(sheet, '_images'):
                for img_obj in sheet._images:
                    img_data = img_obj.ref.getvalue()
                    image = Image.open(io.BytesIO(img_data))
                    images.append(image)
    except Exception as e:
        print(f"画像抽出エラー: {e}")
    return images

@st.cache_resource(show_spinner=False)
def process_uploaded_files(uploaded_files):
    """ファイルを読み込み、テキストのインデックスと画像のリストを返す"""
    with st.spinner(f"🚀 {len(uploaded_files)}つのファイルを分析中..."):
        file_paths = []
        extracted_images = []

        for uploaded_file in uploaded_files:
            uploaded_file.seek(0)
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                # CSV対応 (文字コード自動変換)
                if file_ext == ".csv":
                    try:
                        df = pd.read_csv(uploaded_file)
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding='shift_jis')
                    df.to_csv(tmp_file.name, index=False, encoding='utf-8')
                
                # 画像ファイル
                elif file_ext in [".png", ".jpg", ".jpeg"]:
                    tmp_file.write(uploaded_file.getvalue())
                    uploaded_file.seek(0)
                    extracted_images.append(Image.open(uploaded_file))
                
                # Excel (画像抽出付き)
                elif file_ext == ".xlsx":
                    tmp_file.write(uploaded_file.getvalue())
                    excel_imgs = extract_images_from_excel(tmp_file.name)
                    extracted_images.append(excel_imgs)

                else:
                    tmp_file.write(uploaded_file.getvalue())

                file_paths.append(tmp_file.name)

        # 画像リストの平坦化
        flat_images = []
        for item in extracted_images:
            if isinstance(item, list):
                flat_images.extend(item)
            else:
                flat_images.append(item)

        documents = SimpleDirectoryReader(input_files=file_paths).load_data()
        index = VectorStoreIndex.from_documents(documents)
        
        for path in file_paths:
            os.remove(path)
            
        return index, flat_images