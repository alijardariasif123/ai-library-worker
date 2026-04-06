# File: worker/Dockerfile
# Dockerfile for Python OCR Worker (Flask + Tesseract + pdfplumber)

FROM python:3.11-slim

# Install system dependencies for Tesseract and PDF/image processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy worker source code
COPY ocr_processor.py .

# Expose worker port (matches PORT_WORKER in env, default 5001)
EXPOSE 5001

# Start the Flask worker
CMD ["python", "ocr_processor.py"]
