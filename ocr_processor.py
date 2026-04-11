# import os
# import logging
# from typing import List, Tuple

# from flask import Flask, request, jsonify
# from dotenv import load_dotenv

# import pdfplumber
# from PIL import Image
# import pytesseract
# import requests

# # ==========================
# # 🔧 SETUP
# # ==========================

# load_dotenv()
# app = Flask(__name__)

# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(asctime)s] [%(levelname)s] %(message)s'
# )

# PORT = int(os.environ.get("PORT", 10000))

# # Render compatible path
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# # ==========================
# # 📥 FILE DOWNLOAD (SAFE)
# # ==========================

# def download_file(file_url: str) -> str:
#     try:
#         filename = os.path.basename(file_url.split("?")[0])
#         local_path = f"/tmp/{filename}"

#         logging.info(f"📥 Downloading: {file_url}")

#         response = requests.get(file_url, stream=True, timeout=120)
#         response.raise_for_status()

#         with open(local_path, "wb") as f:
#             for chunk in response.iter_content(8192):
#                 if chunk:
#                     f.write(chunk)

#         return local_path

#     except Exception as e:
#         logging.exception("❌ Download failed")
#         raise Exception(f"Download error: {str(e)}")


# # ==========================
# # 🧠 OCR HELPERS
# # ==========================

# def ocr_pdf(file_path: str) -> Tuple[int, List[str]]:
#     text_per_page = []

#     with pdfplumber.open(file_path) as pdf:
#         for i, page in enumerate(pdf.pages):
#             try:
#                 text = page.extract_text() or ''

#                 if not text.strip():
#                     logging.info(f"⚠️ Page {i+1}: using OCR fallback")
#                     img = page.to_image(resolution=200).original
#                     text = pytesseract.image_to_string(img) or ''

#                 text_per_page.append(text.strip())

#             except Exception as e:
#                 logging.exception(f"❌ Error on page {i+1}")
#                 text_per_page.append('')

#     return len(text_per_page), text_per_page


# def ocr_image(file_path: str) -> Tuple[int, List[str]]:
#     try:
#         img = Image.open(file_path)
#         text = pytesseract.image_to_string(img) or ''
#         return 1, [text.strip()]
#     except Exception as e:
#         logging.exception("❌ Image OCR failed")
#         return 1, [""]


# # def is_pdf(file_path: str) -> bool:
# #     return file_path.lower().endswith('.pdf')

# def is_pdf(file_path: str) -> bool:
#     return file_path.lower().endswith('.pdf') or 'raw/upload' in file_path


# def is_image(file_path: str) -> bool:
#     return any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'])


# # ==========================
# # 🌡 HEALTH CHECK
# # ==========================

# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify({
#         'success': True,
#         'message': 'OCR worker running ✅'
#     }), 200


# # ==========================
# # 🚀 MAIN OCR ENDPOINT (FIXED)
# # ==========================

# @app.route('/process', methods=['POST'])
# def process():
#     temp_file = None

#     try:
#         data = request.get_json(force=True, silent=True) or {}

#         document_id = data.get('documentId')
#         file_url = data.get('fileUrl')   # ✅ FIXED KEY

#         if not document_id or not file_url:
#             return jsonify({
#                 'success': False,
#                 'message': 'documentId and fileUrl are required'
#             }), 400

#         logging.info(f"📄 Processing document: {document_id}")

#         # 🔥 Download file
#         temp_file = download_file(file_url)
#         file_path = temp_file

#         if not os.path.exists(file_path):
#             raise Exception("Downloaded file not found")

#         # ======================
#         # OCR LOGIC
#         # ======================
#         if is_pdf(file_path):
#             pages, text_per_page = ocr_pdf(file_path)
#         elif is_image(file_path):
#             pages, text_per_page = ocr_image(file_path)
#         else:
#             logging.warning("Unknown format → trying PDF")
#             pages, text_per_page = ocr_pdf(file_path)

#         logging.info(f"✅ OCR complete: pages={pages}")

#         return jsonify({
#             'success': True,
#             'documentId': document_id,
#             'pages': pages,
#             'textPerPage': text_per_page
#         }), 200

#     except Exception as e:
#         logging.exception("❌ OCR failed")

#         return jsonify({
#             'success': False,
#             'message': 'OCR processing failed',
#             'error': str(e)
#         }), 500

#     finally:
#         # 🧹 Cleanup
#         if temp_file and os.path.exists(temp_file):
#             try:
#                 os.remove(temp_file)
#                 logging.info("🧹 Temp file deleted")
#             except Exception:
#                 pass


# # ==========================
# # 🚀 START SERVER
# # ==========================

# if __name__ == '__main__':
#     logging.info(f'🚀 OCR server running on port {PORT}')
#     app.run(host='0.0.0.0', port=PORT)
import os
import logging
from typing import List, Tuple

from flask import Flask, request, jsonify
from dotenv import load_dotenv

import pdfplumber
from PIL import Image
import pytesseract
import requests

# ==========================
# 🔧 SETUP
# ==========================

load_dotenv()
app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)

PORT = int(os.environ.get("PORT", 10000))

# Render compatible path
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# ==========================
# 📥 FILE DOWNLOAD (FIXED)
# ==========================

def download_file(file_url: str) -> str:
    try:
        filename = os.path.basename(file_url.split("?")[0]) or "file"
        local_path = f"/tmp/{filename}"

        logging.info(f"📥 Downloading: {file_url}")

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*"
        }

        response = requests.get(file_url, headers=headers, stream=True, timeout=120)

        # 🔥 retry fallback
        if response.status_code == 401:
            logging.warning("⚠️ Unauthorized → retry without headers")
            response = requests.get(file_url, stream=True, timeout=120)

        response.raise_for_status()

        with open(local_path, "wb") as f:
            for chunk in response.iter_content(8192):
                if chunk:
                    f.write(chunk)

        return local_path

    except Exception as e:
        logging.exception("❌ Download failed")
        raise Exception(f"Download error: {str(e)}")


# ==========================
# 🧠 OCR HELPERS
# ==========================

def ocr_pdf(file_path: str) -> Tuple[int, List[str]]:
    text_per_page = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            try:
                text = page.extract_text() or ''

                if not text.strip():
                    logging.info(f"⚠️ Page {i+1}: using OCR fallback")
                    img = page.to_image(resolution=200).original
                    text = pytesseract.image_to_string(img) or ''

                text_per_page.append(text.strip())

            except Exception as e:
                logging.exception(f"❌ Error on page {i+1}")
                text_per_page.append('')

    return len(text_per_page), text_per_page


def ocr_image(file_path: str) -> Tuple[int, List[str]]:
    try:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img) or ''
        return 1, [text.strip()]
    except Exception as e:
        logging.exception("❌ Image OCR failed")
        return 1, [""]


# ==========================
# 📂 FILE TYPE DETECTION (FIXED)
# ==========================

def is_pdf(file_path: str) -> bool:
    return file_path.lower().endswith('.pdf')


def is_image(file_path: str) -> bool:
    return any(file_path.lower().endswith(ext) for ext in [
        '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'
    ])


# ==========================
# 🌡 HEALTH CHECK
# ==========================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'success': True,
        'message': 'OCR worker running ✅'
    }), 200


# ==========================
# 🚀 MAIN OCR ENDPOINT
# ==========================

@app.route('/process', methods=['POST'])
def process():
    temp_file = None

    try:
        data = request.get_json(force=True, silent=True) or {}

        document_id = data.get('documentId')
        file_url = data.get('fileUrl')

        if not document_id or not file_url:
            return jsonify({
                'success': False,
                'message': 'documentId and fileUrl are required'
            }), 400

        logging.info(f"📄 Processing document: {document_id}")

        # ======================
        # DOWNLOAD
        # ======================
        temp_file = download_file(file_url)

        if not os.path.exists(temp_file):
            raise Exception("Downloaded file not found")

        # ======================
        # OCR LOGIC
        # ======================
        if is_pdf(temp_file):
            pages, text_per_page = ocr_pdf(temp_file)
        elif is_image(temp_file):
            pages, text_per_page = ocr_image(temp_file)
        else:
            logging.warning("⚠️ Unknown format → forcing PDF OCR")
            pages, text_per_page = ocr_pdf(temp_file)

        logging.info(f"✅ OCR complete: pages={pages}")

        return jsonify({
            'success': True,
            'documentId': document_id,
            'pages': pages,
            'textPerPage': text_per_page
        }), 200

    except Exception as e:
        logging.exception("❌ OCR failed")

        return jsonify({
            'success': False,
            'message': 'OCR processing failed',
            'error': str(e)
        }), 500

    finally:
        # ======================
        # 🧹 CLEANUP
        # ======================
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logging.info("🧹 Temp file deleted")
            except Exception:
                pass


# ==========================
# 🚀 START SERVER
# ==========================

if __name__ == '__main__':
    logging.info(f'🚀 OCR server running on port {PORT}')
    app.run(host='0.0.0.0', port=PORT)