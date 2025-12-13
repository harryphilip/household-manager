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

