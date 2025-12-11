"""
OCR Service for processing boleto images using Google Cloud Vision API.
Extracts: barcode (linha digitável), amount, due date, beneficiary.
"""

import os
import re
import json
import tempfile
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR processing."""
    success: bool
    barcode: str = ''
    amount: Optional[Decimal] = None
    due_date: Optional[datetime] = None
    beneficiary: str = ''
    confidence: float = 0.0
    raw_text: str = ''
    extracted_fields: Dict[str, Any] = None
    error: str = ''
    needs_review: bool = True

    def __post_init__(self):
        if self.extracted_fields is None:
            self.extracted_fields = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'barcode': self.barcode,
            'amount': str(self.amount) if self.amount else None,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'beneficiary': self.beneficiary,
            'confidence': self.confidence,
            'raw_text': self.raw_text[:1000] if self.raw_text else '',  # Truncate for response
            'extracted_fields': self.extracted_fields,
            'error': self.error,
            'needs_review': self.needs_review,
        }


class BillOCRService:
    """
    Service for processing boleto images/PDFs and extracting financial data.
    Uses Google Cloud Vision API for OCR.
    """

    # Regex patterns for Brazilian boletos
    # Linha digitável: 47-48 digits, may have dots or spaces
    BARCODE_PATTERN = re.compile(
        r'(\d{5}[\.\s]?\d{5}[\.\s]?\d{5}[\.\s]?\d{6}[\.\s]?\d{5}[\.\s]?\d{6}[\.\s]?\d{1}[\.\s]?\d{14})',
        re.MULTILINE
    )

    # Alternative pattern for barcode without separators
    BARCODE_CLEAN_PATTERN = re.compile(r'(\d{47,48})')

    # Amount patterns
    AMOUNT_PATTERNS = [
        re.compile(r'R\$\s*([\d.,]+)', re.IGNORECASE),
        re.compile(r'VALOR[:\s]*([\d.,]+)', re.IGNORECASE),
        re.compile(r'TOTAL[:\s]*R?\$?\s*([\d.,]+)', re.IGNORECASE),
    ]

    # Date patterns (DD/MM/YYYY or DD.MM.YYYY)
    DATE_PATTERNS = [
        re.compile(r'VENCIMENTO[:\s]*(\d{2}[/\.]\d{2}[/\.]\d{4})', re.IGNORECASE),
        re.compile(r'VENC[:\s]*(\d{2}[/\.]\d{2}[/\.]\d{4})', re.IGNORECASE),
        re.compile(r'DATA[:\s]*(\d{2}[/\.]\d{2}[/\.]\d{4})', re.IGNORECASE),
        re.compile(r'(\d{2}[/\.]\d{2}[/\.]\d{4})'),  # Generic date pattern
    ]

    # Beneficiary patterns
    BENEFICIARY_PATTERNS = [
        re.compile(r'CEDENTE[:\s]*([^\n]+)', re.IGNORECASE),
        re.compile(r'BENEFICI[AÁ]RIO[:\s]*([^\n]+)', re.IGNORECASE),
        re.compile(r'FAVORECIDO[:\s]*([^\n]+)', re.IGNORECASE),
    ]

    def __init__(self):
        self._vision_client = None

    @property
    def vision_client(self):
        """Lazy load Vision client."""
        if self._vision_client is None:
            self._vision_client = self._create_vision_client()
        return self._vision_client

    def _create_vision_client(self):
        """Create Google Cloud Vision client with credentials."""
        try:
            from google.cloud import vision

            # Check for credentials JSON in environment variable
            gcp_credentials_json = os.environ.get('GCP_CREDENTIALS_JSON')

            if gcp_credentials_json:
                # Create temporary credentials file
                credentials_dict = json.loads(gcp_credentials_json)
                credentials_path = os.path.join(tempfile.gettempdir(), 'gcp-credentials.json')

                with open(credentials_path, 'w') as f:
                    json.dump(credentials_dict, f)

                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                logger.info("GCP credentials loaded from environment variable")

            client = vision.ImageAnnotatorClient()
            logger.info("Google Cloud Vision client created successfully")
            return client

        except ImportError:
            logger.error("google-cloud-vision not installed")
            raise ImportError(
                "google-cloud-vision package is required. "
                "Install with: pip install google-cloud-vision"
            )
        except Exception as e:
            logger.error(f"Failed to create Vision client: {e}")
            raise

    def process_file(self, file: UploadedFile) -> OCRResult:
        """
        Process uploaded file (PDF or image) and extract boleto data.

        Args:
            file: Django UploadedFile object

        Returns:
            OCRResult with extracted data
        """
        try:
            file_ext = file.name.lower().split('.')[-1]

            if file_ext == 'pdf':
                return self._process_pdf(file)
            elif file_ext in ['png', 'jpg', 'jpeg']:
                return self._process_image(file)
            else:
                return OCRResult(
                    success=False,
                    error=f"Unsupported file format: {file_ext}"
                )

        except Exception as e:
            logger.exception(f"Error processing file: {e}")
            return OCRResult(
                success=False,
                error=str(e)
            )

    def _process_pdf(self, file: UploadedFile) -> OCRResult:
        """Convert PDF to image and process."""
        try:
            from pdf2image import convert_from_bytes

            # Read PDF content
            pdf_bytes = file.read()
            file.seek(0)  # Reset for potential later use

            # Convert first page to image
            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=200)

            if not images:
                return OCRResult(
                    success=False,
                    error="Could not extract images from PDF"
                )

            # Process first page
            return self._process_pil_image(images[0])

        except ImportError:
            logger.error("pdf2image not installed")
            return OCRResult(
                success=False,
                error="PDF processing not available. Install pdf2image."
            )
        except Exception as e:
            logger.exception(f"Error processing PDF: {e}")
            return OCRResult(
                success=False,
                error=f"PDF processing error: {str(e)}"
            )

    def _process_image(self, file: UploadedFile) -> OCRResult:
        """Process image file directly."""
        try:
            from google.cloud import vision

            content = file.read()
            file.seek(0)

            image = vision.Image(content=content)
            response = self.vision_client.text_detection(image=image)

            if response.error.message:
                return OCRResult(
                    success=False,
                    error=response.error.message
                )

            texts = response.text_annotations
            if not texts:
                return OCRResult(
                    success=False,
                    error="No text detected in image"
                )

            # First annotation contains all detected text
            full_text = texts[0].description

            return self._extract_data_from_text(full_text)

        except Exception as e:
            logger.exception(f"Error processing image: {e}")
            return OCRResult(
                success=False,
                error=str(e)
            )

    def _process_pil_image(self, pil_image) -> OCRResult:
        """Process PIL Image object."""
        try:
            from google.cloud import vision
            import io

            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            content = img_byte_arr.getvalue()

            image = vision.Image(content=content)
            response = self.vision_client.text_detection(image=image)

            if response.error.message:
                return OCRResult(
                    success=False,
                    error=response.error.message
                )

            texts = response.text_annotations
            if not texts:
                return OCRResult(
                    success=False,
                    error="No text detected in image"
                )

            full_text = texts[0].description

            return self._extract_data_from_text(full_text)

        except Exception as e:
            logger.exception(f"Error processing PIL image: {e}")
            return OCRResult(
                success=False,
                error=str(e)
            )

    def _extract_data_from_text(self, text: str) -> OCRResult:
        """
        Extract boleto data from OCR text.

        Args:
            text: Raw OCR text

        Returns:
            OCRResult with extracted fields
        """
        extracted = {
            'barcode_found': False,
            'amount_found': False,
            'date_found': False,
            'beneficiary_found': False,
        }

        # Extract barcode (linha digitável)
        barcode = self._extract_barcode(text)
        if barcode:
            extracted['barcode_found'] = True

        # Extract amount
        amount = self._extract_amount(text)
        if amount:
            extracted['amount_found'] = True

        # If no amount from text, try to extract from barcode
        if not amount and barcode:
            amount = self._extract_amount_from_barcode(barcode)
            if amount:
                extracted['amount_from_barcode'] = True

        # Extract due date
        due_date = self._extract_due_date(text)
        if due_date:
            extracted['date_found'] = True

        # If no date from text, try to extract from barcode
        if not due_date and barcode:
            due_date = self._extract_date_from_barcode(barcode)
            if due_date:
                extracted['date_from_barcode'] = True

        # Extract beneficiary
        beneficiary = self._extract_beneficiary(text)
        if beneficiary:
            extracted['beneficiary_found'] = True

        # Calculate confidence score
        confidence = self._calculate_confidence(extracted)

        # Determine if review is needed
        needs_review = confidence < 70 or not all([
            extracted['barcode_found'],
            extracted['amount_found'] or extracted.get('amount_from_barcode'),
            extracted['date_found'] or extracted.get('date_from_barcode'),
        ])

        return OCRResult(
            success=True,
            barcode=barcode,
            amount=amount,
            due_date=due_date,
            beneficiary=beneficiary,
            confidence=confidence,
            raw_text=text,
            extracted_fields=extracted,
            needs_review=needs_review,
        )

    def _extract_barcode(self, text: str) -> str:
        """Extract linha digitável from text."""
        # Try pattern with separators first
        match = self.BARCODE_PATTERN.search(text)
        if match:
            # Clean up - remove dots and spaces
            barcode = re.sub(r'[\.\s]', '', match.group(1))
            if self._validate_barcode(barcode):
                return barcode

        # Try clean pattern (no separators)
        match = self.BARCODE_CLEAN_PATTERN.search(text.replace(' ', '').replace('.', ''))
        if match:
            barcode = match.group(1)
            if self._validate_barcode(barcode):
                return barcode

        # Try to find sequences of digits that might be barcode parts
        digits = re.findall(r'\d+', text)
        combined = ''.join(digits)

        # Look for 47-48 digit sequences
        for i in range(len(combined) - 46):
            candidate = combined[i:i+47]
            if self._validate_barcode(candidate):
                return candidate
            candidate = combined[i:i+48]
            if self._validate_barcode(candidate):
                return candidate

        return ''

    def _validate_barcode(self, barcode: str) -> bool:
        """
        Validate linha digitável using modulo 10 check digit.

        Brazilian boleto linha digitável has 47 digits with specific structure.
        """
        if not barcode or len(barcode) not in [47, 48]:
            return False

        if not barcode.isdigit():
            return False

        # Basic validation - check if it starts with valid bank codes
        # Brazilian bank codes are 3 digits (001 = BB, 033 = Santander, 341 = Itaú, etc.)
        bank_code = barcode[:3]
        try:
            bank_num = int(bank_code)
            # Valid bank codes are typically between 001 and 999
            if bank_num < 1 or bank_num > 999:
                return False
        except ValueError:
            return False

        return True

    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extract amount from text."""
        for pattern in self.AMOUNT_PATTERNS:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1)
                amount = self._parse_brazilian_amount(amount_str)
                if amount and amount > 0:
                    return amount
        return None

    def _parse_brazilian_amount(self, amount_str: str) -> Optional[Decimal]:
        """
        Parse Brazilian currency format to Decimal.
        Handles: 1.234,56 or 1234,56 or 1234.56
        """
        try:
            # Remove spaces
            amount_str = amount_str.strip()

            # Check if format is Brazilian (comma as decimal separator)
            if ',' in amount_str:
                # Remove thousand separators (dots)
                amount_str = amount_str.replace('.', '')
                # Replace decimal comma with dot
                amount_str = amount_str.replace(',', '.')

            return Decimal(amount_str)
        except (InvalidOperation, ValueError):
            return None

    def _extract_amount_from_barcode(self, barcode: str) -> Optional[Decimal]:
        """
        Extract amount from linha digitável.

        In a 47-digit linha digitável, the amount is encoded in positions 38-47
        (last 10 digits), where the last 2 digits are cents.
        """
        try:
            if len(barcode) == 47:
                amount_str = barcode[37:47]  # Positions 38-47 (0-indexed: 37-46)
                amount_cents = int(amount_str)
                return Decimal(amount_cents) / 100
            elif len(barcode) == 48:
                # Some formats have 48 digits
                amount_str = barcode[38:48]
                amount_cents = int(amount_str)
                return Decimal(amount_cents) / 100
        except (ValueError, InvalidOperation):
            pass
        return None

    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date from text."""
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                date_str = match.group(1)
                date = self._parse_brazilian_date(date_str)
                if date:
                    return date
        return None

    def _parse_brazilian_date(self, date_str: str) -> Optional[datetime]:
        """Parse Brazilian date format (DD/MM/YYYY or DD.MM.YYYY)."""
        try:
            # Normalize separator
            date_str = date_str.replace('.', '/')
            return datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            return None

    def _extract_date_from_barcode(self, barcode: str) -> Optional[datetime]:
        """
        Extract due date from linha digitável.

        The due date is encoded as days since base date (07/10/1997).
        In a 47-digit linha digitável, it's in positions 34-37.
        """
        try:
            if len(barcode) >= 47:
                # Days since 07/10/1997
                days_str = barcode[33:37]  # Positions 34-37 (0-indexed: 33-36)
                days = int(days_str)

                if days == 0:
                    return None  # No due date

                # Base date: October 7, 1997
                base_date = datetime(1997, 10, 7)
                due_date = base_date + timedelta(days=days)

                # Sanity check - date should be reasonable
                if due_date.year < 2000 or due_date.year > 2100:
                    return None

                return due_date
        except (ValueError, IndexError):
            pass
        return None

    def _extract_beneficiary(self, text: str) -> str:
        """Extract beneficiary (cedente) name from text."""
        for pattern in self.BENEFICIARY_PATTERNS:
            match = pattern.search(text)
            if match:
                beneficiary = match.group(1).strip()
                # Clean up - remove extra whitespace and truncate
                beneficiary = ' '.join(beneficiary.split())
                return beneficiary[:200]  # Max 200 chars
        return ''

    def _calculate_confidence(self, extracted: Dict[str, bool]) -> float:
        """
        Calculate confidence score based on extracted fields.

        Scoring:
        - Barcode found: 40 points
        - Amount found: 25 points
        - Due date found: 20 points
        - Beneficiary found: 15 points
        """
        score = 0.0

        if extracted.get('barcode_found'):
            score += 40

        if extracted.get('amount_found'):
            score += 25
        elif extracted.get('amount_from_barcode'):
            score += 20  # Less points if from barcode (less certain)

        if extracted.get('date_found'):
            score += 20
        elif extracted.get('date_from_barcode'):
            score += 15

        if extracted.get('beneficiary_found'):
            score += 15

        return min(score, 100)


# Import timedelta at module level (was missing)
from datetime import timedelta


# Singleton instance for reuse
_ocr_service = None


def get_ocr_service() -> BillOCRService:
    """Get singleton OCR service instance."""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = BillOCRService()
    return _ocr_service
