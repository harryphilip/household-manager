# OCR Label Scanning Setup Guide

This guide explains how to set up and use the OCR (Optical Character Recognition) feature for automatically extracting appliance information from label photos.

## Features

- **Photo Upload**: Take or upload a photo of appliance labels/serial number plates
- **Automatic Extraction**: Extracts brand, model number, and serial number from images
- **Auto-Fill Forms**: Automatically fills in the appliance form with extracted information
- **Dual OCR Support**: Uses EasyOCR (more accurate) with Tesseract fallback

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytesseract` - Python wrapper for Tesseract OCR
- `easyocr` - More accurate OCR engine (optional but recommended)

### 2. Install Tesseract OCR

#### macOS
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
```

#### Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Restart terminal/IDE

### 3. Verify Installation

```bash
tesseract --version
```

## Usage

### In the Web Interface

1. **Go to Create/Edit Appliance page**
2. **Upload Label Image**:
   - Click "Upload Label Image" button
   - Take a photo with your device camera or select from files
   - The image will be previewed
3. **Extract Information**:
   - Click "Extract Information" button
   - Wait for processing (may take a few seconds)
   - Extracted information will appear and auto-fill the form fields
4. **Review and Submit**:
   - Review the extracted information
   - Make any necessary corrections
   - Complete the rest of the form and submit

### Best Practices for Photos

- **Lighting**: Ensure good lighting, avoid shadows
- **Focus**: Make sure the text is in focus and sharp
- **Angle**: Take photo straight-on, not at an angle
- **Distance**: Get close enough that text is readable
- **Background**: Plain background helps OCR accuracy
- **Resolution**: Higher resolution images work better

## How It Works

1. **Image Upload**: User uploads/takes a photo
2. **OCR Processing**: 
   - First tries EasyOCR (if available) - more accurate
   - Falls back to Tesseract OCR if EasyOCR fails
3. **Text Extraction**: Extracts all text from the image
4. **Pattern Matching**: Uses regex patterns to identify:
   - Brand names (from common brand list)
   - Model numbers (patterns like "MODEL: XXX")
   - Serial numbers (patterns like "SERIAL: XXX")
5. **Auto-Fill**: Populates form fields with extracted data

## Supported Brands

The system recognizes these common brands:
- Samsung, LG, Whirlpool, Maytag, KitchenAid
- Bosch, GE, General Electric, Frigidaire, Electrolux
- Kenmore, Panasonic, Sharp, Toshiba, Hitachi
- Daikin, Carrier, Trane, Lennox, Rheem
- A.O. Smith, Bradford White

*More brands can be added to the `parse_appliance_info_from_text()` function in `household/utils.py`*

## Troubleshooting

### OCR Not Working

1. **Check Tesseract Installation**:
   ```bash
   tesseract --version
   ```

2. **Check Python Packages**:
   ```bash
   pip list | grep -E "(pytesseract|easyocr)"
   ```

3. **Test OCR Manually**:
   ```python
   from household.utils import extract_text_from_image
   from PIL import Image
   
   image = Image.open('path/to/image.jpg')
   text = extract_text_from_image(image)
   print(text)
   ```

### Poor Extraction Results

- **Improve Image Quality**: Use better lighting, higher resolution
- **Try Different Angle**: Take photo from different angle
- **Check Text Clarity**: Ensure label text is clear and not faded
- **Manual Entry**: If OCR fails, you can always enter information manually

### EasyOCR Not Available

EasyOCR is optional. If not installed, the system will use Tesseract OCR. To install EasyOCR:

```bash
pip install easyocr
```

Note: EasyOCR requires more disk space and may be slower on first use (downloads models).

## API Endpoint

The OCR functionality is also available via API:

**POST** `/appliances/extract-label-info/`

**Request:**
- Content-Type: `multipart/form-data`
- Field: `label_image` (image file)

**Response:**
```json
{
    "success": true,
    "extracted_text": "Full OCR text...",
    "brand": "Samsung",
    "model_number": "RF28R7351SG",
    "serial_number": "SN123456789"
}
```

## Performance Notes

- **First Run**: EasyOCR downloads models on first use (~500MB)
- **Processing Time**: Typically 2-5 seconds per image
- **Image Size**: Larger images take longer but may be more accurate
- **Server Load**: OCR is CPU-intensive, consider async processing for production

## Security Considerations

- Images are stored in `media/appliance_labels/`
- No image data is sent to external services (all processing is local)
- Images are only accessible to authenticated users
- Consider adding image size limits in production

## Future Enhancements

Possible improvements:
- Batch processing multiple images
- Support for more languages
- Machine learning model for better accuracy
- Integration with manufacturer databases
- QR code scanning for appliance labels

