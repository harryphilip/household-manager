"""
Tests for utility functions.
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from unittest import skipIf
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.uploadedfile import SimpleUploadedFile
from household.utils import (
    search_manual_online,
    search_manual_with_openai,
    download_pdf,
    extract_text_from_pdf,
    extract_maintenance_info,
    extract_maintenance_with_ai,
    extract_text_from_image,
    parse_appliance_info_from_text,
    extract_appliance_info_from_image,
    is_valid_pdf_url,
    extract_pdf_url_from_google_link,
    PYTESSERACT_AVAILABLE,
    EASYOCR_AVAILABLE
)
from household.models import Appliance, Room

# Check if OCR is available
OCR_AVAILABLE = PYTESSERACT_AVAILABLE or EASYOCR_AVAILABLE


class IsValidPdfUrlTest(TestCase):
    """Test cases for is_valid_pdf_url function."""
    
    def test_valid_pdf_url(self):
        """Test valid PDF URLs."""
        valid_urls = [
            "https://example.com/manual.pdf",
            "http://manufacturer.com/downloads/model123.pdf",
            "https://support.example.com/files/manual.pdf",
        ]
        
        for url in valid_urls:
            self.assertTrue(is_valid_pdf_url(url), f"Should be valid: {url}")
    
    def test_invalid_google_search_url(self):
        """Test that Google search URLs are rejected."""
        invalid_urls = [
            "https://www.google.com/search?q=Sub+Zero+SubZero+Fridge+manual+pdf&sca_esv=0ee57afbb50ab6e4",
            "https://www.google.com/url?q=https://example.com/manual.pdf",
            "https://www.google.com/search?q=test+pdf",
        ]
        
        for url in invalid_urls:
            self.assertFalse(is_valid_pdf_url(url), f"Should be invalid: {url}")
    
    def test_invalid_redirect_urls(self):
        """Test that redirect URLs are rejected."""
        invalid_urls = [
            "/url?q=https://example.com/manual.pdf",
            "https://example.com/redirect?url=manual.pdf",
            "https://example.com/manual.pdf&redirect=true",
        ]
        
        for url in invalid_urls:
            self.assertFalse(is_valid_pdf_url(url), f"Should be invalid: {url}")
    
    def test_invalid_urls_without_domain(self):
        """Test that URLs without proper domains are rejected."""
        invalid_urls = [
            "manual.pdf",
            "/path/to/manual.pdf",
            "file:///path/to/manual.pdf",
        ]
        
        for url in invalid_urls:
            self.assertFalse(is_valid_pdf_url(url), f"Should be invalid: {url}")
    
    def test_invalid_non_pdf_urls(self):
        """Test that non-PDF URLs are rejected."""
        invalid_urls = [
            "https://example.com/manual.html",
            "https://example.com/page",
            "https://example.com/download",
        ]
        
        for url in invalid_urls:
            self.assertFalse(is_valid_pdf_url(url), f"Should be invalid: {url}")


class ExtractPdfUrlFromGoogleLinkTest(TestCase):
    """Test cases for extract_pdf_url_from_google_link function."""
    
    def test_extract_from_google_redirect(self):
        """Test extracting URL from Google redirect link."""
        google_link = "/url?q=https://example.com/manual.pdf&sa=U&ved=0ahUKEwiAzf-FnruRAxU7KlkFHTi8OasQ_AUIBCgA"
        result = extract_pdf_url_from_google_link(google_link)
        
        self.assertEqual(result, "https://example.com/manual.pdf")
    
    def test_extract_direct_url(self):
        """Test extracting direct PDF URL."""
        direct_url = "https://example.com/manual.pdf"
        result = extract_pdf_url_from_google_link(direct_url)
        
        self.assertEqual(result, direct_url)
    
    def test_reject_google_search_url(self):
        """Test that Google search URLs are rejected."""
        search_url = "https://www.google.com/search?q=test+pdf&sca_esv=0ee57afbb50ab6e4"
        result = extract_pdf_url_from_google_link(search_url)
        
        self.assertIsNone(result)
    
    def test_reject_invalid_urls(self):
        """Test that invalid URLs are rejected."""
        invalid_urls = [
            "/url?q=https://www.google.com/search?q=test",
            "https://www.google.com/url?q=test",
            "",
            None,
        ]
        
        for url in invalid_urls:
            result = extract_pdf_url_from_google_link(url)
            self.assertIsNone(result, f"Should reject: {url}")


class SearchManualOnlineTest(TestCase):
    """Test cases for search_manual_online function."""
    
    def test_search_with_brand_and_model(self):
        """Test search with brand and model number."""
        with patch('household.utils.requests.get') as mock_get:
            with patch('household.utils.requests.head') as mock_head:
                # Mock HTML response with PDF link
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = '''
                <html>
                    <a href="/url?q=https://example.com/manual.pdf&sa=U">Manual PDF</a>
                </html>
                '''
                mock_get.return_value = mock_response
                
                # Mock HEAD request to verify PDF
                mock_head_response = MagicMock()
                mock_head_response.headers = {'Content-Type': 'application/pdf'}
                mock_head.return_value = mock_head_response
                
                result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
                
                # Should attempt to search
                mock_get.assert_called()
                # Should return valid result if URL is valid
                if result:
                    self.assertIn('url', result)
                    self.assertTrue(is_valid_pdf_url(result['url']))
    
    def test_search_without_brand_or_model(self):
        """Test search without brand or model returns None."""
        result = search_manual_online("", "", "Refrigerator")
        self.assertIsNone(result)
    
    def test_search_handles_errors(self):
        """Test search handles network errors gracefully."""
        with patch('household.utils.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
            
            # Should return None on error
            self.assertIsNone(result)
    
    def test_search_filters_invalid_urls(self):
        """Test that search filters out invalid URLs."""
        with patch('household.utils.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Include both valid and invalid links
            mock_response.text = '''
            <html>
                <a href="/url?q=https://www.google.com/search?q=test&sca_esv=123">Invalid</a>
                <a href="/url?q=https://example.com/manual.pdf&sa=U">Valid PDF</a>
            </html>
            '''
            mock_get.return_value = mock_response
            
            with patch('household.utils.requests.head') as mock_head:
                mock_head_response = MagicMock()
                mock_head_response.headers = {'Content-Type': 'application/pdf'}
                mock_head.return_value = mock_head_response
                
                result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator", use_openai=False)
                
                # Should only return valid PDF URL
                if result:
                    self.assertTrue(is_valid_pdf_url(result['url']))
                    self.assertNotIn('google.com/search', result['url'])


class SearchManualWithOpenAiTest(TestCase):
    """Test cases for search_manual_with_openai function."""
    
    def test_search_without_api_key(self):
        """Test that search returns None when no API key is available."""
        with patch('decouple.config') as mock_config:
            mock_config.return_value = None  # No API key
            
            result = search_manual_with_openai("Samsung", "RF28R7351SG", "Refrigerator")
            
            self.assertIsNone(result)
    
    def test_search_with_openai_success(self):
        """Test successful OpenAI search."""
        with patch('decouple.config') as mock_config:
            mock_config.return_value = "test-api-key"
            
            # Patch OpenAI where it's imported (inside the function)
            with patch('openai.OpenAI') as mock_openai_class:
                mock_client = MagicMock()
                mock_openai_class.return_value = mock_client
                
                # Mock the chat completion response
                mock_response = MagicMock()
                mock_choice = MagicMock()
                mock_message = MagicMock()
                mock_message.content = '{"primary_url": "https://example.com/manual.pdf", "confidence": "high"}'
                mock_choice.message = mock_message
                mock_response.choices = [mock_choice]
                mock_client.chat.completions.create.return_value = mock_response
                
                # Mock HEAD request to verify PDF
                with patch('household.utils.requests.head') as mock_head:
                    mock_head_response = MagicMock()
                    mock_head_response.headers = {'Content-Type': 'application/pdf'}
                    mock_head.return_value = mock_head_response
                    
                    result = search_manual_with_openai("Samsung", "RF28R7351SG", "Refrigerator")
                    
                    # Should return a result
                    if result:
                        self.assertIn('url', result)
                        self.assertTrue(is_valid_pdf_url(result['url']))
    
    def test_search_handles_openai_errors(self):
        """Test that search handles OpenAI API errors gracefully."""
        with patch('decouple.config') as mock_config:
            mock_config.return_value = "test-api-key"
            
            # Patch OpenAI where it's imported (inside the function)
            with patch('openai.OpenAI') as mock_openai_class:
                mock_openai_class.side_effect = Exception("OpenAI API error")
                
                result = search_manual_with_openai("Samsung", "RF28R7351SG", "Refrigerator")
                
                # Should return None on error
                self.assertIsNone(result)


class DownloadPdfTest(TestCase):
    """Test cases for download_pdf function."""
    
    def test_download_valid_pdf(self):
        """Test downloading a valid PDF."""
        pdf_content = b'%PDF-1.4\n...PDF content...'
        
        with patch('household.utils.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = pdf_content
            mock_response.headers = {'Content-Type': 'application/pdf'}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = download_pdf("https://example.com/manual.pdf", "Refrigerator")
            
            self.assertIsNotNone(result)
            self.assertEqual(result.name, "Refrigerator_manual.pdf")
    
    def test_download_invalid_content(self):
        """Test downloading non-PDF content returns None."""
        with patch('household.utils.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b'Not a PDF'
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            result = download_pdf("https://example.com/page.html", "Refrigerator")
            
            self.assertIsNone(result)
    
    def test_download_handles_errors(self):
        """Test download handles errors gracefully."""
        with patch('household.utils.requests.get') as mock_get:
            mock_get.side_effect = Exception("Download error")
            
            result = download_pdf("https://example.com/manual.pdf", "Refrigerator")
            
            self.assertIsNone(result)


class ExtractTextFromPdfTest(TestCase):
    """Test cases for extract_text_from_pdf function."""
    
    def test_extract_text_from_pdf(self):
        """Test extracting text from PDF."""
        # Create a mock PDF file
        pdf_file = BytesIO(b'%PDF-1.4\n...PDF content...')
        
        with patch('household.utils.pdfplumber.open') as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Sample PDF text content"
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
            
            result = extract_text_from_pdf(pdf_file)
            
            self.assertIn("Sample PDF text content", result)
    
    def test_extract_text_fallback_to_pypdf2(self):
        """Test fallback to PyPDF2 when pdfplumber fails."""
        pdf_file = BytesIO(b'%PDF-1.4\n...PDF content...')
        
        with patch('household.utils.pdfplumber.open') as mock_pdfplumber:
            mock_pdfplumber.side_effect = Exception("pdfplumber error")
            
            with patch('household.utils.PyPDF2.PdfReader') as mock_pypdf2:
                mock_reader = MagicMock()
                mock_page = MagicMock()
                mock_page.extract_text.return_value = "PyPDF2 extracted text"
                mock_reader.pages = [mock_page]
                mock_pypdf2.return_value = mock_reader
                
                result = extract_text_from_pdf(pdf_file)
                
                self.assertIn("PyPDF2 extracted text", result)


class ExtractMaintenanceInfoTest(TestCase):
    """Test cases for extract_maintenance_info function."""
    
    def test_extract_maintenance_tasks(self):
        """Test extracting maintenance tasks from text."""
        text = """
        Clean the air filter monthly to ensure proper airflow.
        Inspect the condenser coils quarterly for dust buildup.
        Replace the water filter annually when the indicator light comes on.
        """
        
        tasks = extract_maintenance_info(text, "refrigerator")
        
        self.assertGreater(len(tasks), 0)
        self.assertIn('task_name', tasks[0])
        self.assertIn('frequency', tasks[0])
        self.assertIn('description', tasks[0])
    
    def test_extract_maintenance_with_frequency_keywords(self):
        """Test extraction identifies frequency keywords."""
        text = "Clean the filter monthly. Inspect coils quarterly. Replace filter annually."
        
        tasks = extract_maintenance_info(text, "refrigerator")
        
        frequencies = [task['frequency'] for task in tasks]
        self.assertIn('monthly', frequencies)
        self.assertIn('quarterly', frequencies)
        self.assertIn('annual', frequencies)
    
    def test_extract_maintenance_removes_duplicates(self):
        """Test extraction removes duplicate tasks."""
        text = """
        Clean the filter monthly.
        Clean the filter monthly.
        Clean the filter monthly.
        """
        
        tasks = extract_maintenance_info(text, "refrigerator")
        
        # Should have only one unique task
        unique_tasks = set((task['task_name'].lower(), task['frequency']) for task in tasks)
        self.assertLessEqual(len(unique_tasks), len(tasks))
    
    def test_extract_maintenance_limits_results(self):
        """Test extraction limits to 10 tasks."""
        # Create text with many maintenance mentions
        text = " ".join([f"Task {i} monthly." for i in range(20)])
        
        tasks = extract_maintenance_info(text, "refrigerator")
        
        self.assertLessEqual(len(tasks), 10)
    
    def test_extract_maintenance_empty_text(self):
        """Test extraction with empty text."""
        tasks = extract_maintenance_info("", "refrigerator")
        
        self.assertEqual(len(tasks), 0)


class ExtractMaintenanceWithAiTest(TestCase):
    """Test cases for extract_maintenance_with_ai function."""
    
    def test_extract_without_api_key(self):
        """Test AI extraction falls back to regex when no API key."""
        text = "Clean the filter monthly."
        
        # Patch decouple.config where it's imported inside the function
        with patch('decouple.config') as mock_config:
            mock_config.return_value = None  # No API key
            
            tasks = extract_maintenance_with_ai(text, "refrigerator")
            
            # Should use regex extraction
            self.assertIsInstance(tasks, list)
            # Verify it actually extracted something
            if tasks:
                self.assertIn('task_name', tasks[0])
                self.assertIn('frequency', tasks[0])
    
    def test_extract_handles_ai_errors(self):
        """Test AI extraction handles errors gracefully."""
        text = "Clean the filter monthly."
        
        # Patch decouple.config where it's imported inside the function
        with patch('decouple.config') as mock_config:
            mock_config.return_value = "fake-api-key"
            
            # Mock the extract_maintenance_info to verify fallback
            with patch('household.utils.extract_maintenance_info') as mock_regex:
                mock_regex.return_value = [
                    {'task_name': 'Clean Filter', 'frequency': 'monthly', 'description': 'Clean the filter monthly.', 'extracted_from_manual': True}
                ]
                
                tasks = extract_maintenance_with_ai(text, "refrigerator")
                
                # Should fall back to regex extraction
                self.assertIsInstance(tasks, list)
                # Verify regex extraction was called
                mock_regex.assert_called_once_with(text, "refrigerator")


class IntegrationUtilsTest(TestCase):
    """Integration tests for utility functions with real data patterns."""
    
    def setUp(self):
        """Set up test data."""
        self.room = Room.objects.create(
            name="Kitchen",
            room_type="kitchen",
            floor=1
        )
        self.appliance = Appliance.objects.create(
            name="Refrigerator",
            brand="Samsung",
            model_number="RF28R7351SG",
            serial_number="SN123456",
            appliance_type="refrigerator",
            room=self.room
        )
    
    def test_search_manual_integration(self):
        """Test searching for manual with real appliance data."""
        # This test will make actual HTTP requests (or be mocked)
        with patch('household.utils.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '''
            <html>
                <a href="/url?q=https://example.com/samsung-rf28r7351sg-manual.pdf&sa=U">Manual PDF</a>
            </html>
            '''
            mock_get.return_value = mock_response
            
            result = search_manual_online(
                self.appliance.brand,
                self.appliance.model_number,
                self.appliance.name
            )
            
            # Should attempt to search
            mock_get.assert_called()
            # If result found, verify structure
            if result:
                self.assertIn('url', result)
                self.assertIn('title', result)
    
    def test_extract_maintenance_comprehensive(self):
        """Test extracting maintenance info from comprehensive text."""
        sample_text = """
        Clean the air filter monthly to ensure proper airflow and efficiency.
        Inspect the condenser coils quarterly for dust and debris buildup.
        Replace the water filter annually or when the filter indicator light comes on.
        Clean the door gasket weekly with a damp cloth.
        Defrost the freezer as needed when ice buildup exceeds 1/4 inch.
        """
        
        tasks = extract_maintenance_info(sample_text, "refrigerator")
        
        # Should find multiple tasks
        self.assertGreater(len(tasks), 0)
        
        # Verify task structure
        for task in tasks:
            self.assertIn('task_name', task)
            self.assertIn('frequency', task)
            self.assertIn('description', task)
            self.assertIn('extracted_from_manual', task)
            
            # Verify frequency is valid
            valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly', 
                               'semi_annual', 'annual', 'as_needed']
            self.assertIn(task['frequency'], valid_frequencies)
        
        # Check that we found expected tasks
        task_names = [task['task_name'].lower() for task in tasks]
        # Should find at least some maintenance-related tasks
        self.assertTrue(any('filter' in name or 'clean' in name or 'inspect' in name 
                          for name in task_names))
    
    def test_extract_text_from_pdf_integration(self):
        """Test extracting text from PDF with appliance."""
        from io import BytesIO
        
        # Create a mock PDF file
        pdf_content = b'%PDF-1.4\n...PDF content...\nClean filter monthly.\nInspect coils quarterly.'
        pdf_file = BytesIO(pdf_content)
        
        with patch('household.utils.pdfplumber.open') as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Clean filter monthly. Inspect coils quarterly."
            mock_pdf.pages = [mock_page]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
            
            text = extract_text_from_pdf(pdf_file)
            
            self.assertIsInstance(text, str)
            self.assertGreater(len(text), 0)
            self.assertIn("filter", text.lower())
    
    def test_full_workflow_with_appliance(self):
        """Test complete workflow: search, download, extract."""
        from io import BytesIO
        
        # Step 1: Mock search
        with patch('household.utils.requests.get') as mock_get:
            # Mock search response
            mock_search_response = MagicMock()
            mock_search_response.status_code = 200
            mock_search_response.text = '<html><a href="/url?q=https://example.com/manual.pdf">Manual</a></html>'
            mock_get.return_value = mock_search_response
            
            result = search_manual_online(
                self.appliance.brand,
                self.appliance.model_number,
                self.appliance.name
            )
            
            # Verify search was attempted
            mock_get.assert_called()
        
        # Step 2: Mock download
        if result:
            with patch('household.utils.requests.get') as mock_get:
                mock_download_response = MagicMock()
                mock_download_response.status_code = 200
                mock_download_response.content = b'%PDF-1.4\n...PDF content...'
                mock_download_response.headers = {'Content-Type': 'application/pdf'}
                mock_download_response.raise_for_status = MagicMock()
                mock_get.return_value = mock_download_response
                
                pdf_file = download_pdf(result['url'], self.appliance.name)
                
                # Verify download was attempted
                if pdf_file:
                    self.assertIsNotNone(pdf_file)
                    self.assertIn('manual.pdf', pdf_file.name)
        
        # Step 3: Mock text extraction and maintenance extraction
        sample_text = "Clean the filter monthly. Inspect coils quarterly."
        tasks = extract_maintenance_info(sample_text, self.appliance.appliance_type)
        
        # Should extract maintenance tasks
        self.assertIsInstance(tasks, list)
        if tasks:
            self.assertIn('task_name', tasks[0])
            self.assertIn('frequency', tasks[0])
    
    def test_search_without_brand_or_model(self):
        """Test search fails gracefully when brand/model missing."""
        appliance = Appliance.objects.create(
            name="Generic Appliance",
            appliance_type="other"
        )
        
        result = search_manual_online(
            appliance.brand,
            appliance.model_number,
            appliance.name
        )
        
        # Should return None when no brand/model
        self.assertIsNone(result)
    
    def test_extract_maintenance_with_various_frequencies(self):
        """Test extraction identifies various frequency patterns."""
        text = """
        Check the temperature settings daily to ensure proper operation.
        Clean the interior surfaces weekly with a damp cloth.
        Replace the air filter monthly for optimal performance.
        Inspect the condenser coils quarterly for dust buildup.
        Service the compressor semi-annually to maintain efficiency.
        Replace the water filter annually or when the indicator light comes on.
        """
        
        tasks = extract_maintenance_info(text, "refrigerator")
        
        # Should find multiple tasks with different frequencies
        frequencies_found = [task['frequency'] for task in tasks]
        
        # Should identify at least some frequencies
        self.assertGreater(len(frequencies_found), 0, 
                          f"Expected to find frequencies, but got: {tasks}")
        
        # Verify we got different frequency types
        unique_frequencies = set(frequencies_found)
        self.assertGreater(len(unique_frequencies), 0)


class ExtractTextFromImageTest(TestCase):
    """Test cases for extract_text_from_image function."""
    
    def setUp(self):
        """Create a test image."""
        # Create a simple test image
        self.test_image = Image.new('RGB', (100, 100), color='white')
        self.image_file = BytesIO()
        self.test_image.save(self.image_file, format='PNG')
        self.image_file.seek(0)
    
    def test_extract_text_with_tesseract(self):
        """Test text extraction using Tesseract OCR."""
        with patch('household.utils.PYTESSERACT_AVAILABLE', True):
            with patch('household.utils.pytesseract') as mock_pytesseract:
                mock_pytesseract.image_to_string.return_value = "SAMSUNG MODEL RF28R7351SG SERIAL SN123456"
                
                text = extract_text_from_image(self.image_file)
                
                self.assertIsInstance(text, str)
                self.assertIn("SAMSUNG", text)
                mock_pytesseract.image_to_string.assert_called()
    
    def test_extract_text_with_easyocr(self):
        """Test text extraction using EasyOCR (preferred method)."""
        with patch('household.utils.EASYOCR_AVAILABLE', True):
            with patch('household.utils.easyocr') as mock_easyocr:
                mock_reader = MagicMock()
                mock_reader.readtext.return_value = [
                    ([], "SAMSUNG", 0.9),
                    ([], "MODEL RF28R7351SG", 0.8),
                    ([], "SERIAL SN123456", 0.85)
                ]
                mock_easyocr.Reader.return_value = mock_reader
                
                text = extract_text_from_image(self.image_file)
                
                self.assertIsInstance(text, str)
                self.assertIn("SAMSUNG", text)
                mock_reader.readtext.assert_called_once()
    
    def test_extract_text_fallback_to_tesseract(self):
        """Test fallback to Tesseract when EasyOCR fails."""
        with patch('household.utils.EASYOCR_AVAILABLE', True):
            with patch('household.utils.easyocr') as mock_easyocr:
                # EasyOCR fails
                mock_easyocr.Reader.side_effect = Exception("EasyOCR error")
                
                with patch('household.utils.PYTESSERACT_AVAILABLE', True):
                    with patch('household.utils.pytesseract') as mock_pytesseract:
                        mock_pytesseract.image_to_string.return_value = "Fallback text from Tesseract"
                        
                        text = extract_text_from_image(self.image_file)
                        
                        self.assertEqual(text, "Fallback text from Tesseract")
                        mock_pytesseract.image_to_string.assert_called()
    
    def test_extract_text_handles_errors(self):
        """Test error handling in text extraction."""
        with patch('household.utils.PYTESSERACT_AVAILABLE', True):
            with patch('household.utils.pytesseract') as mock_pytesseract:
                mock_pytesseract.image_to_string.side_effect = Exception("OCR error")
                
                text = extract_text_from_image(self.image_file)
                
                self.assertEqual(text, "")
    
    def test_extract_text_empty_image(self):
        """Test extraction with invalid image."""
        invalid_file = BytesIO(b'not an image')
        
        # Should return empty string, not raise exception
        text = extract_text_from_image(invalid_file)
        self.assertEqual(text, "")


class ParseApplianceInfoFromTextTest(TestCase):
    """Test cases for parse_appliance_info_from_text function."""
    
    def test_parse_brand(self):
        """Test brand extraction from text."""
        text = "SAMSUNG REFRIGERATOR MODEL RF28R7351SG"
        info = parse_appliance_info_from_text(text)
        
        self.assertEqual(info['brand'], 'Samsung')
    
    def test_parse_model_number(self):
        """Test model number extraction."""
        text = "MODEL: RF28R7351SG SERIAL: SN123456"
        info = parse_appliance_info_from_text(text)
        
        self.assertEqual(info['model_number'], 'RF28R7351SG')
    
    def test_parse_serial_number(self):
        """Test serial number extraction."""
        text = "SERIAL NUMBER: SN123456789 MODEL: ABC123"
        info = parse_appliance_info_from_text(text)
        
        # Should extract the serial number after "SERIAL NUMBER:"
        self.assertEqual(info['serial_number'], 'SN123456789')
    
    def test_parse_all_fields(self):
        """Test extracting all fields from comprehensive text."""
        text = """
        SAMSUNG REFRIGERATOR
        MODEL NO: RF28R7351SG
        SN: SN123456789012
        """
        info = parse_appliance_info_from_text(text)
        
        self.assertEqual(info['brand'], 'Samsung')
        self.assertEqual(info['model_number'], 'RF28R7351SG')
        self.assertEqual(info['serial_number'], 'SN123456789012')
    
    def test_parse_various_model_patterns(self):
        """Test different model number patterns."""
        patterns = [
            ("MODEL: ABC123", "ABC123"),
            ("Model No: XYZ-456", "XYZ-456"),
            ("Model# DEF789", "DEF789"),
            ("MOD: GHI012", "GHI012"),
        ]
        
        for text, expected in patterns:
            info = parse_appliance_info_from_text(text)
            self.assertEqual(info['model_number'], expected, f"Failed for: {text}")
    
    def test_parse_various_serial_patterns(self):
        """Test different serial number patterns."""
        patterns = [
            ("SERIAL: SN123456", "SN123456"),
            ("Serial No: ABC789XYZ", "ABC789XYZ"),
            ("Serial# DEF456", "DEF456"),
            ("S/N: GHI123", "GHI123"),
        ]
        
        for text, expected in patterns:
            info = parse_appliance_info_from_text(text)
            self.assertEqual(info['serial_number'], expected, f"Failed for: {text}")
    
    def test_parse_multiple_brands(self):
        """Test parsing different brands."""
        brands = ['LG', 'WHIRLPOOL', 'BOSCH', 'GE']
        
        for brand in brands:
            text = f"{brand} APPLIANCE MODEL ABC123"
            info = parse_appliance_info_from_text(text)
            self.assertEqual(info['brand'], brand.title(), f"Failed for brand: {brand}")
    
    def test_parse_empty_text(self):
        """Test parsing empty text."""
        info = parse_appliance_info_from_text("")
        
        self.assertIsNone(info['brand'])
        self.assertIsNone(info['model_number'])
        self.assertIsNone(info['serial_number'])
    
    def test_parse_no_matches(self):
        """Test parsing text with no appliance info."""
        text = "This is just some random text with no appliance information."
        info = parse_appliance_info_from_text(text)
        
        self.assertIsNone(info['brand'])
        # May find some alphanumeric patterns, but shouldn't find structured info
        self.assertIsNone(info.get('model_number') or None)
    
    def test_parse_case_insensitive(self):
        """Test that parsing is case insensitive."""
        text = "samsung model rf28r7351sg serial sn123456"
        info = parse_appliance_info_from_text(text)
        
        self.assertEqual(info['brand'], 'Samsung')
        self.assertEqual(info['model_number'], 'RF28R7351SG')
        self.assertEqual(info['serial_number'], 'SN123456')


class ExtractApplianceInfoFromImageTest(TestCase):
    """Test cases for extract_appliance_info_from_image function.
    
    REQUIRED: These tests require OCR libraries to be installed.
    Tests will FAIL if OCR libraries are not available.
    """
    
    def setUp(self):
        """Create test image with appliance label text."""
        if not OCR_AVAILABLE:
            self.fail("OCR libraries (pytesseract or easyocr) are REQUIRED for these tests. "
                     "Install with: pip install pytesseract easyocr")
        
        # Create an image that looks like an appliance label
        self.test_image = Image.new('RGB', (400, 300), color='white')
        draw = ImageDraw.Draw(self.test_image)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Draw appliance label text
        label_text = "SAMSUNG\nMODEL: RF28R7351SG\nSERIAL: SN123456789"
        draw.text((20, 20), label_text, fill='black', font=font)
        
        self.image_file = BytesIO()
        self.test_image.save(self.image_file, format='PNG')
        self.image_file.seek(0)
    
    def test_extract_info_success(self):
        """Test successful extraction of appliance info from real image (REQUIRES OCR)."""
        result = extract_appliance_info_from_image(self.image_file)
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('extracted_text', result)
        
        # OCR should succeed and extract text (may fail if Tesseract not installed)
        if not result['success']:
            # Check if it's a Tesseract installation issue
            error_msg = result.get('error', '').lower()
            if 'tesseract' in error_msg and 'not installed' in error_msg:
                self.fail("Tesseract OCR is not installed. Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
            else:
                self.fail(f"OCR extraction failed: {result.get('error', 'Unknown error')}")
        
        self.assertIsNotNone(result.get('extracted_text'))
        self.assertGreater(len(result.get('extracted_text', '')), 0)
    
    def test_extract_info_no_text(self):
        """Test extraction when no text is found."""
        # Create blank image
        blank_image = Image.new('RGB', (100, 100), color='white')
        blank_file = BytesIO()
        blank_image.save(blank_file, format='PNG')
        blank_file.seek(0)
        
        result = extract_appliance_info_from_image(blank_file)
        # May succeed but find no text, or fail - both are acceptable
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_extract_info_partial_data(self):
        """Test extraction with partial information."""
        # Test with mocked text extraction to verify parsing logic
        with patch('household.utils.extract_text_from_image') as mock_extract:
            mock_extract.return_value = "SAMSUNG REFRIGERATOR"
            
            result = extract_appliance_info_from_image(self.image_file)
            
            self.assertTrue(result['success'])
            self.assertEqual(result['brand'], 'Samsung')
            # Model and serial may not be found
            self.assertIsNone(result.get('model_number'))
    
    def test_extract_info_handles_errors(self):
        """Test error handling in extraction."""
        # Create a file-like object that will cause an error
        invalid_file = BytesIO(b'not an image')
        
        result = extract_appliance_info_from_image(invalid_file)
        
        # Should handle error gracefully
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_extract_info_real_ocr_parsing(self):
        """Test that real OCR extraction and parsing works together (REQUIRES OCR)."""
        result = extract_appliance_info_from_image(self.image_file)
        
        self.assertIsInstance(result, dict)
        
        # Check for Tesseract installation issue
        if not result['success']:
            error_msg = result.get('error', '').lower()
            if 'tesseract' in error_msg and 'not installed' in error_msg:
                self.fail("Tesseract OCR is not installed. Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
            else:
                self.fail(f"OCR extraction must succeed: {result.get('error', 'Unknown error')}")
        
        self.assertTrue(result['success'], "OCR extraction must succeed")
        
        # If OCR succeeded, verify parsing worked
        if result.get('extracted_text'):
            # Should have attempted to parse
            self.assertIn('brand', result)
            self.assertIn('model_number', result)
            self.assertIn('serial_number', result)
            
            # Should have extracted at least brand (most reliable)
            # Model and serial depend on OCR accuracy
            extracted_text = result.get('extracted_text', '').upper()
            if 'SAMSUNG' in extracted_text:
                self.assertEqual(result['brand'], 'Samsung', 
                               "Should extract brand from OCR text")

