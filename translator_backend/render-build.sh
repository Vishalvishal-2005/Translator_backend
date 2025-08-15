#!/bin/bash

# Update package list
apt-get update

# Install Tesseract OCR and Tamil language data
apt-get install -y tesseract-ocr tesseract-ocr-tam

# Install Python dependencies
pip install -r translator_backend/requirements.txt
