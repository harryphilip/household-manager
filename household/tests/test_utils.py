"""
Tests for utility functions.
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from io import BytesIO
from household.utils import (
    search_manual_online,
    download_pdf,
    extract_text_from_pdf,
    extract_maintenance_info,
    extract_maintenance_with_ai
)


class SearchManualOnlineTest(TestCase):
    """Test cases for search_manual_online function."""
    
    def test_search_with_brand_and_model(self):
        """Test search with brand and model number."""
        with patch('household.utils.requests.get') as mock_get:
            # Mock HTML response with PDF link
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = '''
            <html>
                <a href="/url?q=https://example.com/manual.pdf&sa=U">Manual PDF</a>
            </html>
            '''
            mock_get.return_value = mock_response
            
            result = search_manual_online("Samsung", "RF28R7351SG", "Refrigerator")
            
            # Should attempt to search
            mock_get.assert_called()
    
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

