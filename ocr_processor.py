# # File: worker/ocr_processor.py

# import os
# import logging
# from typing import List, Tuple

# from flask import Flask, request, jsonify
# from dotenv import load_dotenv

# import pdfplumber
# from PIL import Image
# import pytesseract
# import requests   # 🔥 NEW (remote file download ke liye)

# # ==========================
# # 🔧 SETUP
# # ==========================

# load_dotenv()

# app = Flask(__name__)

# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(asctime)s] [%(levelname)s] %(message)s'
# )

# # 🔥 FIXED: Render compatible PORT
# PORT = int(os.environ.get("PORT", 5001))

# # 🔥 FIXED: Tesseract path (Render compatible)
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# # ==========================
# # 📥 FILE HANDLING (NEW)
# # ==========================

# def download_file(file_url: str) -> str:
#     """
#     Download remote file and save locally in /tmp
#     """
#     local_path = f"/tmp/{os.path.basename(file_url)}"

#     response = requests.get(file_url)
#     if response.status_code != 200:
#         raise Exception(f"Failed to download file from URL: {file_url}")

#     with open(local_path, "wb") as f:
#         f.write(response.content)

#     return local_path


# # ==========================
# # 🧠 OCR HELPERS
# # ==========================

# def ocr_pdf(file_path: str) -> Tuple[int, List[str]]:
#     text_per_page = []

#     with pdfplumber.open(file_path) as pdf:
#         for page_index, page in enumerate(pdf.pages):
#             try:
#                 page_text = page.extract_text() or ''
#                 page_text = page_text.strip()

#                 if not page_text:
#                     logging.info(f'Page {page_index + 1}: using image OCR fallback')
#                     img = page.to_image(resolution=200).original
#                     page_text = pytesseract.image_to_string(img) or ''

#                 text_per_page.append(page_text.strip())

#             except Exception as e:
#                 logging.exception(f'Error page {page_index + 1}: {e}')
#                 text_per_page.append('')

#     return len(text_per_page), text_per_page


# def ocr_image(file_path: str) -> Tuple[int, List[str]]:
#     img = Image.open(file_path)
#     text = pytesseract.image_to_string(img) or ''
#     return 1, [text.strip()]


# def is_pdf(file_path: str) -> bool:
#     return file_path.lower().endswith('.pdf')


# def is_image(file_path: str) -> bool:
#     exts = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp']
#     return any(file_path.lower().endswith(ext) for ext in exts)


# # ==========================
# # 🌡 HEALTH CHECK
# # ==========================

# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify({
#         'success': True,
#         'message': 'OCR worker is running ✅'
#     }), 200


# # ==========================
# # 📥 MAIN OCR ENDPOINT
# # ==========================

# @app.route('/process', methods=['POST'])
# def process():
#     try:
#         data = request.get_json(force=True, silent=True) or {}
#         document_id = data.get('documentId')
#         file_path = data.get('filePath')

#         if not document_id or not file_path:
#             return jsonify({
#                 'success': False,
#                 'message': 'documentId and filePath are required.'
#             }), 400

#         logging.info(f'Received OCR request: {document_id}')

#         # 🔥 FIX: handle remote URL
#         if file_path.startswith("http"):
#             logging.info(f'Downloading file from URL: {file_path}')
#             file_path = download_file(file_path)

#         if not os.path.exists(file_path):
#             return jsonify({
#                 'success': False,
#                 'documentId': document_id,
#                 'message': f'File not found: {file_path}'
#             }), 404

#         # OCR processing
#         if is_pdf(file_path):
#             pages, text_per_page = ocr_pdf(file_path)
#         elif is_image(file_path):
#             pages, text_per_page = ocr_image(file_path)
#         else:
#             try:
#                 pages, text_per_page = ocr_pdf(file_path)
#             except Exception:
#                 pages, text_per_page = ocr_image(file_path)

#         text_per_page = [t or '' for t in text_per_page]

#         logging.info(f'OCR done: {document_id} | pages={pages}')

#         return jsonify({
#             'success': True,
#             'documentId': document_id,
#             'pages': pages,
#             'textPerPage': text_per_page
#         }), 200

#     except Exception as e:
#         logging.exception('OCR failed')
#         return jsonify({
#             'success': False,
#             'message': 'OCR processing failed',
#             'error': str(e)
#         }), 500


# # ==========================
# # 🚀 MAIN
# # ==========================

# if __name__ == '__main__':
#     logging.info(f'Starting OCR worker on port {PORT}...')
#     app.run(host='0.0.0.0', port=PORT)


# File: worker/ocr_processor.py

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

# PORT = int(os.environ.get("PORT", 5001))

# # Render compatible path
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# # ==========================
# # 📥 FILE DOWNLOAD (FIXED)
# # ==========================

# def download_file(file_url: str) -> str:
#     """
#     Download remote file safely using streaming
#     """
#     filename = os.path.basename(file_url.split("?")[0])
#     local_path = f"/tmp/{filename}"

#     logging.info(f"Downloading file: {file_url}")

#     try:
#         response = requests.get(file_url, stream=True, timeout=60)
#         response.raise_for_status()

#         with open(local_path, "wb") as f:
#             for chunk in response.iter_content(chunk_size=8192):
#                 if chunk:
#                     f.write(chunk)

#         return local_path

#     except Exception as e:
#         logging.exception("File download failed")
#         raise Exception(f"Download failed: {str(e)}")


# # ==========================
# # 🧠 OCR HELPERS
# # ==========================

# def ocr_pdf(file_path: str) -> Tuple[int, List[str]]:
#     text_per_page = []

#     with pdfplumber.open(file_path) as pdf:
#         for page_index, page in enumerate(pdf.pages):
#             try:
#                 page_text = page.extract_text() or ''
#                 page_text = page_text.strip()

#                 if not page_text:
#                     logging.info(f'Page {page_index + 1}: fallback to OCR')
#                     img = page.to_image(resolution=200).original
#                     page_text = pytesseract.image_to_string(img) or ''

#                 text_per_page.append(page_text.strip())

#             except Exception as e:
#                 logging.exception(f'Error page {page_index + 1}')
#                 text_per_page.append('')

#     return len(text_per_page), text_per_page


# def ocr_image(file_path: str) -> Tuple[int, List[str]]:
#     try:
#         img = Image.open(file_path)
#         text = pytesseract.image_to_string(img) or ''
#         return 1, [text.strip()]
#     except Exception as e:
#         logging.exception("Image OCR failed")
#         return 1, [""]


# def is_pdf(file_path: str) -> bool:
#     return file_path.lower().endswith('.pdf')


# def is_image(file_path: str) -> bool:
#     return any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'])


# # ==========================
# # 🌡 HEALTH CHECK
# # ==========================

# @app.route('/health', methods=['GET'])
# def health():
#     return jsonify({
#         'success': True,
#         'message': 'OCR worker is running ✅'
#     }), 200


# # ==========================
# # 📥 MAIN OCR ENDPOINT
# # ==========================

# @app.route('/process', methods=['POST'])
# def process():
#     temp_file = None

#     try:
#         data = request.get_json(force=True, silent=True) or {}
#         document_id = data.get('documentId')
#         file_path = data.get('filePath')

#         if not document_id or not file_path:
#             return jsonify({
#                 'success': False,
#                 'message': 'documentId and filePath are required.'
#             }), 400

#         logging.info(f'OCR request: {document_id}')

#         # 🔥 Handle remote URL
#         if file_path.startswith("http"):
#             temp_file = download_file(file_path)
#             file_path = temp_file

#         if not os.path.exists(file_path):
#             return jsonify({
#                 'success': False,
#                 'message': f'File not found: {file_path}'
#             }), 404

#         # OCR
#         if is_pdf(file_path):
#             pages, text_per_page = ocr_pdf(file_path)
#         elif is_image(file_path):
#             pages, text_per_page = ocr_image(file_path)
#         else:
#             try:
#                 pages, text_per_page = ocr_pdf(file_path)
#             except:
#                 pages, text_per_page = ocr_image(file_path)

#         text_per_page = [t or '' for t in text_per_page]

#         logging.info(f'OCR done: {document_id}, pages={pages}')

#         return jsonify({
#             'success': True,
#             'documentId': document_id,
#             'pages': pages,
#             'textPerPage': text_per_page
#         }), 200

#     except Exception as e:
#         logging.exception("OCR failed")
#         return jsonify({
#             'success': False,
#             'message': 'OCR processing failed',
#             'error': str(e)
#         }), 500

#     finally:
#         # 🔥 CLEANUP TEMP FILE (VERY IMPORTANT)
#         if temp_file and os.path.exists(temp_file):
#             try:
#                 os.remove(temp_file)
#                 logging.info(f"Deleted temp file: {temp_file}")
#             except Exception as e:
#                 logging.warning(f"Failed to delete temp file: {temp_file}")
                

# # ==========================
# # 🚀 MAIN
# # ==========================

# if __name__ == '__main__':
#     logging.info(f'Starting OCR worker on port {PORT}...')
#     app.run(host='0.0.0.0', port=PORT)

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
# # 📥 FILE DOWNLOAD
# # ==========================

# def download_file(file_url: str) -> str:
#     filename = os.path.basename(file_url.split("?")[0])
#     local_path = f"/tmp/{filename}"

#     logging.info(f"📥 Downloading: {file_url}")

#     response = requests.get(file_url, stream=True, timeout=60)
#     response.raise_for_status()

#     with open(local_path, "wb") as f:
#         for chunk in response.iter_content(8192):
#             if chunk:
#                 f.write(chunk)

#     return local_path


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
#                     logging.info(f"Page {i+1}: OCR fallback")
#                     img = page.to_image(resolution=200).original
#                     text = pytesseract.image_to_string(img) or ''

#                 text_per_page.append(text.strip())

#             except Exception as e:
#                 logging.exception(f"Error page {i+1}")
#                 text_per_page.append('')

#     return len(text_per_page), text_per_page


# def ocr_image(file_path: str) -> Tuple[int, List[str]]:
#     try:
#         img = Image.open(file_path)
#         text = pytesseract.image_to_string(img) or ''
#         return 1, [text.strip()]
#     except Exception as e:
#         logging.exception("Image OCR failed")
#         return 1, [""]


# def is_pdf(file_path: str) -> bool:
#     return file_path.lower().endswith('.pdf')


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
#     })


# # ==========================
# # 🚀 MAIN OCR ENDPOINT (FIXED)
# # ==========================

# @app.route('/process', methods=['POST'])
# def process():
#     temp_file = None

#     try:
#         data = request.get_json(force=True) or {}

#         document_id = data.get('documentId')
#         file_url = data.get('fileUrl')  # 🔥 FIX HERE

#         if not document_id or not file_url:
#             return jsonify({
#                 'success': False,
#                 'message': 'documentId and fileUrl required'
#             }), 400

#         logging.info(f"📄 Processing: {document_id}")

#         # 🔥 Download file
#         temp_file = download_file(file_url)
#         file_path = temp_file

#         if not os.path.exists(file_path):
#             return jsonify({
#                 'success': False,
#                 'message': 'File not found after download'
#             }), 500

#         # OCR
#         if is_pdf(file_path):
#             pages, text_per_page = ocr_pdf(file_path)
#         elif is_image(file_path):
#             pages, text_per_page = ocr_image(file_path)
#         else:
#             pages, text_per_page = ocr_pdf(file_path)

#         logging.info(f"✅ OCR done: {document_id}")

#         return jsonify({
#             'success': True,
#             'pages': pages,
#             'textPerPage': text_per_page
#         })

#     except Exception as e:
#         logging.exception("❌ OCR failed")

#         return jsonify({
#             'success': False,
#             'message': str(e)
#         }), 500

#     finally:
#         if temp_file and os.path.exists(temp_file):
#             try:
#                 os.remove(temp_file)
#                 logging.info(f"🧹 Temp deleted")
#             except:
#                 pass


# # ==========================
# # 🚀 START
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
# 📥 FILE DOWNLOAD (SAFE)
# ==========================

def download_file(file_url: str) -> str:
    try:
        filename = os.path.basename(file_url.split("?")[0])
        local_path = f"/tmp/{filename}"

        logging.info(f"📥 Downloading: {file_url}")

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


# def is_pdf(file_path: str) -> bool:
#     return file_path.lower().endswith('.pdf')

def is_pdf(file_path: str) -> bool:
    return file_path.lower().endswith('.pdf') or 'raw/upload' in file_path


def is_image(file_path: str) -> bool:
    return any(file_path.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'])


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
# 🚀 MAIN OCR ENDPOINT (FIXED)
# ==========================

@app.route('/process', methods=['POST'])
def process():
    temp_file = None

    try:
        data = request.get_json(force=True, silent=True) or {}

        document_id = data.get('documentId')
        file_url = data.get('fileUrl')   # ✅ FIXED KEY

        if not document_id or not file_url:
            return jsonify({
                'success': False,
                'message': 'documentId and fileUrl are required'
            }), 400

        logging.info(f"📄 Processing document: {document_id}")

        # 🔥 Download file
        temp_file = download_file(file_url)
        file_path = temp_file

        if not os.path.exists(file_path):
            raise Exception("Downloaded file not found")

        # ======================
        # OCR LOGIC
        # ======================
        if is_pdf(file_path):
            pages, text_per_page = ocr_pdf(file_path)
        elif is_image(file_path):
            pages, text_per_page = ocr_image(file_path)
        else:
            logging.warning("Unknown format → trying PDF")
            pages, text_per_page = ocr_pdf(file_path)

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
        # 🧹 Cleanup
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