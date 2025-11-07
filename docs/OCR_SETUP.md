# OCR Setup Guide

The application now supports Optical Character Recognition (OCR) for scanned images and image-based PDFs.

## What is OCR?

OCR (Optical Character Recognition) allows the app to extract text from images. This means you can:
- Upload scanned medical reports (JPG, PNG images)
- Upload PDFs that contain scanned pages (image-based PDFs)
- The app will automatically detect if text extraction is needed and use OCR

## Installation

### Step 1: Install Python Packages

The required packages are already in `requirements.txt`:
```bash
pip install pytesseract Pillow
```

### Step 2: Install Tesseract OCR Engine

**Windows:**
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (recommended: install to `C:\Program Files\Tesseract-OCR`)
3. Add Tesseract to your PATH, or the app will try to find it automatically

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Linux (Fedora):**
```bash
sudo dnf install tesseract
```

### Step 3: Verify Installation

After installing, restart your Streamlit app. The OCR functionality will be available automatically.

## How It Works

1. **Text-based PDF**: Extracts text directly (fast)
2. **Image-based PDF**: If text extraction fails, automatically uses OCR on each page
3. **Image files**: Directly uses OCR to extract text

## Supported Formats

- **PDFs**: Both text-based and scanned/image-based
- **Images**: PNG, JPG, JPEG, GIF, BMP

## Tips for Best Results

1. **Image Quality**: Clear, high-resolution images work best
2. **Text Orientation**: Text should be horizontal and readable
3. **Lighting**: Well-lit documents scan better
4. **Language**: Currently supports English (can be extended to other languages)

## Troubleshooting

**Error: "OCR libraries not installed"**
- Install: `pip install pytesseract Pillow`

**Error: "Tesseract not found"**
- Make sure Tesseract OCR engine is installed on your system
- On Windows, you may need to add it to PATH or specify the path manually

**Poor OCR Results:**
- Ensure the image is clear and high resolution
- Check that text is not rotated or distorted
- Try scanning at a higher DPI (300 DPI recommended)

## Manual Tesseract Path Configuration (Windows)

If Tesseract is not automatically detected, you can set the path in the code:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

This is usually not needed as the app will try to find Tesseract automatically.


