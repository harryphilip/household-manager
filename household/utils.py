"""
Utility functions for web search, PDF processing, and maintenance extraction.
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
import PyPDF2
import pdfplumber
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image

# Optional OCR imports
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr = None


def search_manual_online(brand, model_number, appliance_name):
    """
    Search for appliance manual online.
    Returns a dictionary with 'url' and 'title' if found.
    """
    if not brand and not model_number:
        return None
    
    # Build search query
    query_parts = []
    if brand:
        query_parts.append(brand)
    if model_number:
        query_parts.append(model_number)
    if appliance_name:
        query_parts.append(appliance_name)
    
    query = " ".join(query_parts) + " manual pdf"
    search_query = quote_plus(query)
    
    # Try multiple search strategies
    search_urls = [
        f"https://www.google.com/search?q={search_query}&tbm=isch&tbs=ift:pdf",
        f"https://www.google.com/search?q={search_query}+filetype:pdf",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for search_url in search_urls:
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for PDF links
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if 'pdf' in href.lower() or 'manual' in href.lower():
                        # Extract actual URL from Google's redirect
                        if href.startswith('/url?q='):
                            actual_url = href.split('/url?q=')[1].split('&')[0]
                        else:
                            actual_url = href
                        
                        # Verify it's a PDF
                        if actual_url.lower().endswith('.pdf') or 'pdf' in actual_url.lower():
                            return {
                                'url': actual_url,
                                'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                            }
        except Exception as e:
            print(f"Error searching: {e}")
            continue
    
    return None


def download_pdf(url, appliance_name):
    """
    Download a PDF from a URL and return it as a Django file.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower():
            # Check first bytes
            first_bytes = response.content[:4]
            if first_bytes != b'%PDF':
                return None
        
        # Create a filename
        filename = f"{appliance_name.replace(' ', '_')}_manual.pdf"
        
        # Return as Django ContentFile
        return ContentFile(response.content, name=filename)
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return None


def extract_text_from_pdf(pdf_file):
    """
    Extract text from a PDF file.
    Returns the extracted text as a string.
    """
    text = ""
    
    try:
        # Try pdfplumber first (better for complex PDFs)
        pdf_file.seek(0)
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        try:
            # Fallback to PyPDF2
            pdf_file.seek(0)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    return text


def extract_maintenance_info(text, appliance_type=None):
    """
    Extract maintenance information from manual text.
    Returns a list of maintenance task dictionaries.
    """
    tasks = []
    
    # Common maintenance keywords and patterns
    maintenance_patterns = [
        (r'clean[^.]*?(?:monthly|weekly|daily|quarterly|annually|yearly)', re.IGNORECASE),
        (r'maintain[^.]*?(?:monthly|weekly|daily|quarterly|annually|yearly)', re.IGNORECASE),
        (r'inspect[^.]*?(?:monthly|weekly|daily|quarterly|annually|yearly)', re.IGNORECASE),
        (r'replace[^.]*?(?:monthly|weekly|daily|quarterly|annually|yearly)', re.IGNORECASE),
        (r'filter[^.]*?(?:monthly|weekly|daily|quarterly|annually|yearly)', re.IGNORECASE),
        (r'lubricat[^.]*?(?:monthly|weekly|daily|quarterly|annually|yearly)', re.IGNORECASE),
    ]
    
    # Frequency mapping
    frequency_map = {
        'daily': 'daily',
        'weekly': 'weekly',
        'monthly': 'monthly',
        'quarterly': 'quarterly',
        'semi-annual': 'semi_annual',
        'semi annual': 'semi_annual',
        'annually': 'annual',
        'yearly': 'annual',
        'year': 'annual',
    }
    
    # Split text into sentences
    sentences = re.split(r'[.!?]\s+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # Skip very short sentences
            continue
        
        # Check for maintenance-related content
        for pattern, flags in maintenance_patterns:
            match = re.search(pattern, sentence, flags)
            if match:
                # Extract frequency
                frequency = 'monthly'  # default
                for freq_key, freq_value in frequency_map.items():
                    if freq_key in sentence.lower():
                        frequency = freq_value
                        break
                
                # Extract task name (first few words)
                words = sentence.split()[:5]
                task_name = ' '.join(words)
                if len(task_name) > 50:
                    task_name = task_name[:47] + "..."
                
                # Clean up task name
                task_name = re.sub(r'[^\w\s-]', '', task_name)
                
                tasks.append({
                    'task_name': task_name or 'Maintenance Task',
                    'description': sentence[:500],  # Limit description length
                    'frequency': frequency,
                    'extracted_from_manual': True,
                })
                break
    
    # Remove duplicates
    seen = set()
    unique_tasks = []
    for task in tasks:
        key = (task['task_name'].lower(), task['frequency'])
        if key not in seen:
            seen.add(key)
            unique_tasks.append(task)
    
    return unique_tasks[:10]  # Limit to 10 tasks


def extract_maintenance_with_ai(text, appliance_type=None):
    """
    Use AI to extract maintenance information (optional, requires OpenAI API key).
    Falls back to regex extraction if API key is not available.
    """
    from decouple import config
    import openai
    
    api_key = config('OPENAI_API_KEY', default=None)
    if not api_key:
        return extract_maintenance_info(text, appliance_type)
    
    try:
        openai.api_key = api_key
        prompt = f"""Extract maintenance tasks from this appliance manual text. 
        For each maintenance task, provide:
        1. Task name (short, clear)
        2. Description
        3. Frequency (daily, weekly, monthly, quarterly, semi-annual, annual, or as needed)
        4. Estimated duration in minutes
        5. Difficulty level (easy, medium, hard, or professional)
        
        Appliance type: {appliance_type or 'Unknown'}
        
        Manual text:
        {text[:4000]}  # Limit to avoid token limits
        
        Return as a structured list. If no maintenance tasks found, return empty list."""
        
        # Note: This is a simplified example. You'd need to use the actual OpenAI API
        # For now, fall back to regex extraction
        return extract_maintenance_info(text, appliance_type)
    except Exception as e:
        print(f"AI extraction error: {e}")
        return extract_maintenance_info(text, appliance_type)


def extract_text_from_image(image_file):
    """
    Extract text from an image using OCR.
    Returns the extracted text as a string.
    """
    text = ""
    
    try:
        # Open and process image
        image = Image.open(image_file)
        
        # Try EasyOCR first (more accurate but slower)
        if EASYOCR_AVAILABLE:
            try:
                import numpy as np
                # Convert PIL Image to numpy array for EasyOCR
                img_array = np.array(image)
                reader = easyocr.Reader(['en'], gpu=False)
                results = reader.readtext(img_array)
                text = ' '.join([result[1] for result in results])
                if text:
                    return text
            except Exception as e:
                print(f"EasyOCR error: {e}, falling back to Tesseract")
        
        # Fallback to Tesseract OCR
        if PYTESSERACT_AVAILABLE:
            try:
                text = pytesseract.image_to_string(image, lang='eng')
            except Exception as e:
                print(f"Tesseract OCR error: {e}")
                # If pytesseract is not configured, try basic OCR
                try:
                    text = pytesseract.image_to_string(image)
                except Exception as e2:
                    print(f"OCR failed: {e2}")
                    return ""
        else:
            print("OCR libraries not available. Please install pytesseract or easyocr.")
            return ""
        
        return text.strip()
    except Exception as e:
        print(f"Error processing image: {e}")
        return ""


def parse_appliance_info_from_text(text):
    """
    Parse appliance information (brand, model, serial number) from OCR text.
    Returns a dictionary with extracted information.
    """
    if not text:
        return {
            'brand': None,
            'model_number': None,
            'serial_number': None,
        }
    
    # Normalize text - remove extra whitespace, convert to uppercase for matching
    normalized_text = ' '.join(text.split())
    text_upper = normalized_text.upper()
    
    info = {
        'brand': None,
        'model_number': None,
        'serial_number': None,
    }
    
    # Common brand patterns (add more as needed)
    brands = [
        'SAMSUNG', 'LG', 'WHIRLPOOL', 'MAYTAG', 'KITCHENAID', 'BOSCH', 
        'GE', 'GENERAL ELECTRIC', 'FRIGIDAIRE', 'ELECTROLUX', 'KENMORE',
        'PANASONIC', 'SHARP', 'TOSHIBA', 'HITACHI', 'DAIKIN', 'CARRIER',
        'TRANE', 'LENNOX', 'RHEEM', 'A.O. SMITH', 'BRADFORD WHITE'
    ]
    
    # Find brand
    for brand in brands:
        if brand in text_upper:
            info['brand'] = brand.title()
            break
    
    # Model number patterns (usually alphanumeric, often contains dashes)
    # Common patterns: MODEL: XXX, Model No: XXX, Model# XXX, etc.
    model_patterns = [
        r'MODEL[:\s#]+([A-Z0-9\-]+)',
        r'MODEL\s+NO[:\s#]+([A-Z0-9\-]+)',
        r'MODEL\s+NUMBER[:\s#]+([A-Z0-9\-]+)',
        r'MOD[:\s#]+([A-Z0-9\-]+)',
    ]
    
    for pattern in model_patterns:
        match = re.search(pattern, text_upper, re.IGNORECASE)
        if match:
            model = match.group(1).strip()
            # Filter out very short or invalid model numbers
            if len(model) >= 3 and len(model) <= 30:
                info['model_number'] = model
                break
    
    # Serial number patterns (more specific to avoid matching "NUMBER" as serial)
    # Order matters - check SN and S/N first (more specific)
    serial_patterns = [
        (r'SN[:\s#]+([A-Z0-9\-]{5,50})', True),  # SN: followed by alphanumeric
        (r'S/N[:\s#]+([A-Z0-9\-]{5,50})', True),  # S/N: followed by alphanumeric
        (r'SERIAL\s+NO[:\s#]+([A-Z0-9\-]{5,50})', True),  # SERIAL NO: followed by alphanumeric
        (r'SERIAL[:\s#]+([A-Z0-9\-]{5,50})', True),  # SERIAL: followed by alphanumeric
        (r'SERIAL\s+NUMBER[:\s#]+([A-Z0-9\-]{5,50})', True),  # SERIAL NUMBER: followed by alphanumeric
    ]
    
    for pattern, _ in serial_patterns:
        match = re.search(pattern, text_upper, re.IGNORECASE)
        if match:
            serial = match.group(1).strip()
            # Additional validation: should not be just "NUMBER" or common words
            if serial and serial not in ['NUMBER', 'NO', 'NUM'] and len(serial) >= 5:
                info['serial_number'] = serial
                break
    
    # If no model found with patterns, try to find alphanumeric codes
    if not info['model_number']:
        # Look for patterns like: ABC123, ABC-123, ABC123-XYZ
        model_candidate = re.search(r'\b([A-Z]{2,4}[-]?[0-9]{3,6}[A-Z0-9\-]*)\b', text_upper)
        if model_candidate:
            candidate = model_candidate.group(1)
            if 5 <= len(candidate) <= 20:
                info['model_number'] = candidate
    
    # If no serial found, look for long alphanumeric strings
    if not info['serial_number']:
        # Look for longer alphanumeric strings (serial numbers are usually longer)
        serial_candidate = re.search(r'\b([A-Z0-9]{8,20})\b', text_upper)
        if serial_candidate:
            candidate = serial_candidate.group(1)
            # Make sure it's not the model number
            if candidate != info.get('model_number', ''):
                info['serial_number'] = candidate
    
    return info


def extract_appliance_info_from_image(image_file):
    """
    Complete workflow: Extract text from image and parse appliance information.
    Returns a dictionary with brand, model_number, and serial_number.
    """
    # Extract text from image
    text = extract_text_from_image(image_file)
    
    if not text:
        return {
            'success': False,
            'error': 'Could not extract text from image. Please ensure the image is clear and readable.',
            'extracted_text': '',
            'brand': None,
            'model_number': None,
            'serial_number': None,
        }
    
    # Parse information from text
    info = parse_appliance_info_from_text(text)
    
    return {
        'success': True,
        'extracted_text': text,
        'brand': info.get('brand'),
        'model_number': info.get('model_number'),
        'serial_number': info.get('serial_number'),
    }

