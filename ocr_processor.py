# File: worker/ocr_processor.py
# Python OCR Worker (Flask)
# - Accepts a JSON payload with { documentId, filePath }
# - Detects if file is PDF or image
# - Uses pdfplumber for PDFs
# - Uses Pillow + pytesseract for images
# - Returns JSON: { success, documentId, pages, textPerPage }
#
# NOTE:
# - This worker is called synchronously from Node (queue/processor.js)
# - It does NOT push data back to backend itself; it just returns the OCR result.
# - Make sure the backend and worker containers share the same volume for filePath.

import os
import io
import logging
from typing import List, Tuple

from flask import Flask, request, jsonify
from dotenv import load_dotenv

import pdfplumber
from PIL import Image
import pytesseract

# ==========================
# 🔧 SETUP
# ==========================

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)

PORT = int(os.getenv('PORT_WORKER', '5001'))

# If tesseract is in a custom path, set it here:
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'


# ==========================
# 🧠 OCR HELPERS
# ==========================

def ocr_pdf(file_path: str) -> Tuple[int, List[str]]:
  """
  Extract text from each page of a PDF using pdfplumber + Tesseract fallback.
  Returns (pages_count, [textPerPage])
  """
  text_per_page = []

  with pdfplumber.open(file_path) as pdf:
    for page_index, page in enumerate(pdf.pages):
      try:
        # First try pdfplumber's built-in text extractor
        page_text = page.extract_text() or ''
        page_text = page_text.strip()

        # If no text, fallback to image-based OCR
        if not page_text:
          logging.info(f'Page {page_index + 1}: no extracted text, using image-based OCR')
          img = page.to_image(resolution=200).original
          page_text = pytesseract.image_to_string(img) or ''

        text_per_page.append(page_text.strip())
      except Exception as e:
        logging.exception(f'Error processing page {page_index + 1}: {e}')
        text_per_page.append('')  # Keep page count consistent

  return len(text_per_page), text_per_page


def ocr_image(file_path: str) -> Tuple[int, List[str]]:
  """
  Extract text from single image using Tesseract.
  Returns (1, [text])
  """
  img = Image.open(file_path)
  text = pytesseract.image_to_string(img) or ''
  return 1, [text.strip()]


def is_pdf(file_path: str) -> bool:
  return file_path.lower().endswith('.pdf')


def is_image(file_path: str) -> bool:
  exts = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp']
  return any(file_path.lower().endswith(ext) for ext in exts)


# ==========================
# 🌡 HEALTH CHECK
# ==========================

@app.route('/health', methods=['GET'])
def health():
  return jsonify({
      'success': True,
      'message': 'OCR worker is up and running ✅'
  }), 200


# ==========================
# 📥 MAIN OCR ENDPOINT
# ==========================

@app.route('/process', methods=['POST'])
def process():
  """
  Expects JSON: { "documentId": "...", "filePath": "..." }
  Responds with:
  {
    "success": true/false,
    "documentId": "...",
    "pages": <int>,
    "textPerPage": ["...", "..."],
    "error": "optional error message"
  }
  """
  try:
    data = request.get_json(force=True, silent=True) or {}
    document_id = data.get('documentId')
    file_path = data.get('filePath')

    if not document_id or not file_path:
      return jsonify({
          'success': False,
          'message': 'documentId and filePath are required.'
      }), 400

    if not os.path.exists(file_path):
      logging.error(f'File not found for OCR: {file_path}')
      return jsonify({
          'success': False,
          'documentId': document_id,
          'message': f'File not found: {file_path}'
      }), 404

    logging.info(f'Starting OCR for documentId={document_id}, filePath={file_path}')

    if is_pdf(file_path):
      pages, text_per_page = ocr_pdf(file_path)
    elif is_image(file_path):
      pages, text_per_page = ocr_image(file_path)
    else:
      # Try PDF first; if fails, try image as fallback
      try:
        pages, text_per_page = ocr_pdf(file_path)
      except Exception:
        pages, text_per_page = ocr_image(file_path)

    # Basic cleanup: ensure length match
    text_per_page = [t if t is not None else '' for t in text_per_page]

    logging.info(
        f'OCR complete for documentId={document_id} | pages={pages}'
    )

    return jsonify({
        'success': True,
        'documentId': document_id,
        'pages': pages,
        'textPerPage': text_per_page
    }), 200

  except Exception as e:
    logging.exception('Error in /process OCR endpoint')
    return jsonify({
        'success': False,
        'message': 'OCR processing failed.',
        'error': str(e)
    }), 500


# ==========================
# 🚀 MAIN
# ==========================

if __name__ == '__main__':
  logging.info(f'Starting OCR worker on port {PORT}...')
  app.run(host='0.0.0.0', port=PORT)
