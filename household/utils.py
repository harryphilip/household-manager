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


def is_valid_pdf_url(url):
    """
    Validate that a URL is a proper PDF URL with a domain.
    Returns True if valid, False otherwise.
    """
    if not url:
        return False
    
    # Decode URL if encoded
    try:
        from urllib.parse import unquote
        url = unquote(url)
    except:
        pass
    
    # Must start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Must have a domain (not just a path)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.netloc or not parsed.netloc.count('.'):
            return False
    except:
        return False
    
    # Must not be a Google search URL
    if 'google.com/search' in url.lower() or 'google.com/url' in url.lower():
        return False
    
    # Must not be a redirect URL pattern
    # Check for Google redirect patterns specifically: /url?q= or /url?url=
    # These are Google's redirect URL formats, not legitimate query parameters
    if '/url?q=' in url or '/url?url=' in url:
        return False
    # Check for redirect URLs in path, but allow legitimate query parameters
    # Only reject if 'redirect' appears in the path (e.g., /redirect?url=...) not in query params
    parsed_url = urlparse(url)
    if 'redirect' in parsed_url.path.lower():
        return False
    
    # Should end with .pdf or have pdf in the path
    # Check the path part (before query parameters) for .pdf
    parsed_url = urlparse(url)
    path_lower = parsed_url.path.lower()
    url_lower = url.lower()  # Keep for search parameter checks
    # Accept URLs that end with .pdf in path or have /pdf/ in path
    # Note: We don't accept URLs just because they're from known manual sites,
    # as those sites may have non-PDF pages (like support pages)
    has_pdf_indicator = (path_lower.endswith('.pdf') or '/pdf' in path_lower)
    
    if not has_pdf_indicator:
        return False
    
    # Must not contain search query parameters
    if 'search?q=' in url_lower or 'sca_esv=' in url_lower or 'source=lnms' in url_lower:
        return False
    
    return True


def extract_pdf_url_from_google_link(href):
    """
    Extract actual PDF URL from Google search result link.
    Returns the actual URL or None if invalid.
    """
    if not href:
        return None
    
    # Handle Google redirect URLs (multiple formats)
    if href.startswith('/url?q='):
        # Extract the actual URL from Google's redirect
        try:
            from urllib.parse import unquote, parse_qs, urlparse
            # Get the q parameter value
            actual_url = href.split('/url?q=')[1].split('&')[0]
            actual_url = unquote(actual_url)
            
            # Validate it's a proper PDF URL
            if is_valid_pdf_url(actual_url):
                return actual_url
        except:
            pass
    
    # Handle /url?url= format (another Google redirect format)
    if '/url?' in href and 'url=' in href:
        try:
            from urllib.parse import unquote, parse_qs, urlparse
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            if 'url' in params:
                actual_url = params['url'][0]
                actual_url = unquote(actual_url)
                if is_valid_pdf_url(actual_url):
                    return actual_url
        except:
            pass
    
    # Handle direct links
    if href.startswith('http://') or href.startswith('https://'):
        if is_valid_pdf_url(href):
            return href
    
    return None


def search_manual_online(brand, model_number, appliance_name, debug=False, use_openai=True):
    """
    Search for appliance manual online.
    Tries OpenAI first (if available), then falls back to web scraping.
    Returns a dictionary with 'url' and 'title' if found.
    Only returns valid PDF URLs with proper domains (not search URLs).
    
    Args:
        brand: Brand name of the appliance
        model_number: Model number of the appliance
        appliance_name: Name/type of appliance
        debug: If True, print debug information
        use_openai: If True, try OpenAI first (requires OPENAI_API_KEY)
    
    Returns:
        Dictionary with 'url' and 'title' if found, None otherwise
    """
    if not brand and not model_number:
        return None
    
    if debug:
        print(f"Searching for manual: {brand} {model_number} {appliance_name}")
    
    # Define headers early so they can be used in all strategies
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Strategy 0: Try OpenAI first (if enabled and API key available)
    if use_openai:
        if debug:
            print("Trying OpenAI search...")
        openai_result = search_manual_with_openai(brand, model_number, appliance_name)
        if openai_result:
            if debug:
                print(f"OpenAI found: {openai_result.get('url')}")
            return openai_result
        elif debug:
            print("OpenAI search did not find a manual")
    
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
    # Strategy 1: Try manufacturer website directly (for known brands)
    manufacturer_sites = {
        'sub zero': 'https://www.subzero-wolf.com',
        'subzero': 'https://www.subzero-wolf.com',
        'sub-zero': 'https://www.subzero-wolf.com',
    }
    
    brand_lower = brand.lower() if brand else ''
    if brand_lower in manufacturer_sites:
        base_url = manufacturer_sites[brand_lower]
        # Try common manual paths
        manual_paths = [
            f"{base_url}/support/manuals",
            f"{base_url}/manuals",
            f"{base_url}/support",
        ]
        for path in manual_paths:
            try:
                response = requests.get(path, headers=headers, timeout=5)
                if response.status_code == 200:
                    # Look for PDF links on the page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link.get('href', '')
                        # Make absolute URL if relative
                        if href.startswith('/'):
                            href = base_url + href
                        elif not href.startswith('http'):
                            continue
                        
                        # Check if it's a PDF and matches model
                        if ('.pdf' in href.lower() and 
                            (model_number.lower() in href.lower() or model_number.lower() in link.get_text().lower())):
                            if is_valid_pdf_url(href):
                                return {
                                    'url': href,
                                    'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                                }
            except:
                continue
    
    # Strategy 2: Try manual library sites
    manual_library_sites = [
        f"https://www.manualslib.com/search.html?q={quote_plus(f'{brand} {model_number}')}",
        f"https://www.manualsonline.com/search.html?q={quote_plus(f'{brand} {model_number}')}",
    ]
    
    for lib_url in manual_library_sites:
        try:
            response = requests.get(lib_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for PDF download links
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    # Make absolute if relative
                    if href.startswith('/'):
                        from urllib.parse import urlparse
                        parsed = urlparse(lib_url)
                        href = f"{parsed.scheme}://{parsed.netloc}{href}"
                    
                    if '.pdf' in href.lower() and is_valid_pdf_url(href):
                        return {
                            'url': href,
                            'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                        }
        except:
            continue
    
    # Strategy 3: Google search (may be blocked)
    # Note: Google may block automated searches, but we try anyway
    search_urls = [
        f"https://www.google.com/search?q={search_query}+filetype:pdf",
        f"https://www.google.com/search?q={search_query}&tbm=isch&tbs=ift:pdf",
        # Try with site: restriction to manufacturer sites
        f"https://www.google.com/search?q={quote_plus(brand)}+{quote_plus(model_number)}+manual+site:subzero-wolf.com+filetype:pdf" if brand and 'sub' in brand_lower else None,
    ]
    # Filter out None values
    search_urls = [url for url in search_urls if url]
    
    for search_url in search_urls:
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                found_urls = set()  # Track found URLs to avoid duplicates
                
                # Strategy 1: Look for links with href containing /url?q= or data-ved (Google result links)
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    
                    # Skip if it's clearly a search URL
                    if '/search?q=' in href or href.startswith('/search'):
                        continue
                    
                    # Extract actual PDF URL from Google link
                    actual_url = extract_pdf_url_from_google_link(href)
                    
                    if actual_url and actual_url not in found_urls:
                        found_urls.add(actual_url)
                        
                        # Verify it's actually a PDF
                        try:
                            # Make a HEAD request to verify it's a PDF
                            head_response = requests.head(actual_url, headers=headers, timeout=5, allow_redirects=True)
                            content_type = head_response.headers.get('Content-Type', '').lower()
                            
                            # Check if it's a PDF
                            if 'pdf' in content_type or actual_url.lower().endswith('.pdf'):
                                return {
                                    'url': actual_url,
                                    'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                                }
                        except Exception as head_error:
                            # If HEAD fails, still accept if URL looks valid and ends with .pdf
                            if actual_url.lower().endswith('.pdf'):
                                return {
                                    'url': actual_url,
                                    'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                                }
                
                # Strategy 2: Look for direct PDF links in the page text/HTML
                # Sometimes PDFs are embedded or linked differently
                page_text = response.text
                
                # Look for PDF URLs in the raw HTML using regex
                import re
                pdf_url_patterns = [
                    r'https?://[^\s<>"\'\)]+\.pdf(?:\?[^\s<>"\'\)]*)?',
                    r'https?://[^\s<>"\'\)]+/[^\s<>"\'\)]*pdf[^\s<>"\'\)]*(?:\.pdf)?',
                ]
                
                for pattern in pdf_url_patterns:
                    matches = re.findall(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        # Clean up the URL (remove trailing characters and decode)
                        from urllib.parse import unquote
                        url = match.split('"')[0].split("'")[0].split('>')[0].split('<')[0].split(')')[0].rstrip('.,;')
                        url = unquote(url)
                        
                        if is_valid_pdf_url(url) and url not in found_urls:
                            found_urls.add(url)
                            try:
                                # Verify it's a PDF
                                head_response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
                                content_type = head_response.headers.get('Content-Type', '').lower()
                                
                                if 'pdf' in content_type:
                                    return {
                                        'url': url,
                                        'title': f"{brand} {model_number} Manual"
                                    }
                            except:
                                # If HEAD fails but URL looks valid, accept it
                                if url.lower().endswith('.pdf'):
                                    return {
                                        'url': url,
                                        'title': f"{brand} {model_number} Manual"
                                    }
                
                # Strategy 3: Look for data-ved attributes which Google uses for result links
                # These often contain the actual URLs in data attributes
                result_divs = soup.find_all('div', {'data-ved': True})
                for div in result_divs:
                    # Look for links within these divs
                    inner_links = div.find_all('a', href=True)
                    for link in inner_links:
                        href = link.get('href', '')
                        actual_url = extract_pdf_url_from_google_link(href)
                        if actual_url and actual_url not in found_urls:
                            found_urls.add(actual_url)
                            if actual_url.lower().endswith('.pdf'):
                                try:
                                    head_response = requests.head(actual_url, headers=headers, timeout=5, allow_redirects=True)
                                    content_type = head_response.headers.get('Content-Type', '').lower()
                                    if 'pdf' in content_type:
                                        return {
                                            'url': actual_url,
                                            'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                                        }
                                except:
                                    if actual_url.lower().endswith('.pdf'):
                                        return {
                                            'url': actual_url,
                                            'title': link.get_text().strip() or f"{brand} {model_number} Manual"
                                        }
        except Exception as e:
            if debug:
                print(f"Error searching {search_url}: {e}")
            continue
    
    # If no manual found, return None
    if debug:
        print("No manual found through automated search")
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


def search_manual_with_openai(brand, model_number, appliance_name):
    """
    Use OpenAI to find appliance manual URLs.
    Leverages OpenAI's knowledge to suggest where manuals are typically hosted.
    Returns a dictionary with 'url' and 'title' if found.
    Only returns valid PDF URLs. If only a manufacturer support URL is found,
    returns None (caller should handle this case appropriately).
    """
    from decouple import config
    
    api_key = config('OPENAI_API_KEY', default=None)
    if not api_key:
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        prompt = f"""Find the user manual PDF URL for this appliance:
- Brand: {brand}
- Model Number: {model_number}
- Appliance Type: {appliance_name or 'Unknown'}

Based on your knowledge, provide:
1. The most likely URL where the manual PDF can be found (manufacturer website, manual library, etc.)
2. Alternative URLs if the first one doesn't work
3. The official manufacturer support/manual page URL

Return ONLY a valid PDF URL (must end with .pdf or be a direct link to a PDF file).
If you cannot find a specific URL, return the manufacturer's support/manual page URL where the user can search.

Format your response as a JSON object with this structure:
{{
    "primary_url": "https://example.com/manual.pdf",
    "alternative_urls": ["https://alt1.com/manual.pdf"],
    "manufacturer_support_url": "https://manufacturer.com/support/manuals",
    "confidence": "high|medium|low"
}}

If you cannot find a PDF URL, set primary_url to null and provide the manufacturer_support_url."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using cheaper model for this task
            messages=[
                {"role": "system", "content": "You are a helpful assistant that finds appliance manual PDF URLs. Always return valid URLs in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse the response
        content = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        import json
        import re
        
        # Look for JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            try:
                result = json.loads(json_match.group())
                
                # Try primary URL first
                if result.get('primary_url') and is_valid_pdf_url(result['primary_url']):
                    # Verify it's actually a PDF
                    try:
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        head_response = requests.head(result['primary_url'], headers=headers, timeout=5, allow_redirects=True)
                        content_type = head_response.headers.get('Content-Type', '').lower()
                        
                        if 'pdf' in content_type or result['primary_url'].lower().endswith('.pdf'):
                            return {
                                'url': result['primary_url'],
                                'title': f"{brand} {model_number} Manual"
                            }
                    except Exception as head_error:
                        # If HEAD fails, still accept if URL looks valid
                        if result['primary_url'].lower().endswith('.pdf'):
                            return {
                                'url': result['primary_url'],
                                'title': f"{brand} {model_number} Manual"
                            }
                
                # Try alternative URLs
                for alt_url in result.get('alternative_urls', []):
                    if is_valid_pdf_url(alt_url):
                        try:
                            headers = {
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                            head_response = requests.head(alt_url, headers=headers, timeout=5, allow_redirects=True)
                            content_type = head_response.headers.get('Content-Type', '').lower()
                            if 'pdf' in content_type or alt_url.lower().endswith('.pdf'):
                                return {
                                    'url': alt_url,
                                    'title': f"{brand} {model_number} Manual"
                                }
                        except:
                            if alt_url.lower().endswith('.pdf'):
                                return {
                                    'url': alt_url,
                                    'title': f"{brand} {model_number} Manual"
                                }
                
                # If no PDF URL found but we have manufacturer support URL
                # Return it with a note so the view can handle it appropriately
                # The view will validate and show a helpful message to the user
                if result.get('manufacturer_support_url'):
                    support_url = result['manufacturer_support_url']
                    # Validate it's at least a valid URL (even if not a PDF)
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(support_url)
                        if parsed.scheme in ('http', 'https') and parsed.netloc:
                            return {
                                'url': support_url,
                                'title': f"{brand} {model_number} Manual (Support Page)",
                                'note': f'This is the manufacturer support page. Please search for model {model_number} on that page to find the manual PDF.'
                            }
                    except:
                        pass
                    # If URL is invalid, return None
                    return None
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract URL from text
                url_pattern = r'https?://[^\s<>"]+\.pdf'
                matches = re.findall(url_pattern, content)
                for match in matches:
                    if is_valid_pdf_url(match):
                        return {
                            'url': match,
                            'title': f"{brand} {model_number} Manual"
                        }
        
        return None
        
    except Exception as e:
        print(f"OpenAI search error: {e}")
        return None


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

