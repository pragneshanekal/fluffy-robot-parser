"""
Complete Labs 0-3 Implementation for Project LANTERN
Combines all labs into a unified pipeline for SEC filing processing.
"""

import fitz  # PyMuPDF
import pdfplumber
import camelot
import json
import logging
import pandas as pd
import numpy as np
import cv2
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from enum import Enum
import subprocess
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
    
# =============================================================================
# LAB 1: TEXT EXTRACTION  
# =============================================================================

@dataclass
class WordBox:
    """Word with bounding box coordinates."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_num: int
    confidence: float = 1.0

@dataclass
class PageText:
    """Text content of a single page."""
    page_num: int
    text: str
    word_boxes: List[WordBox]
    width: float
    height: float
    extraction_method: str
    quality_score: float

@dataclass
class DocumentText:
    """Complete document text extraction."""
    filename: str
    total_pages: int
    pages: List[PageText]
    extraction_stats: Dict[str, Any]
    processed_at: str

class OptimizedTextExtractor:
    """Lab 1: Multi-library text extraction with quality-based fallback."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.quality_threshold = config.get("quality_threshold", 0.7)
    
    def extract_document(self, pdf_path: Path) -> DocumentText:
        """Extract text from entire PDF document."""
        logger.info(f"Lab 1: Extracting text from {pdf_path.name}")
        
        pages = []
        extraction_stats = {"pdfplumber": 0, "pymupdf": 0, "ocr": 0, "total_words": 0}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_result = self._extract_page_pdfplumber(page, page_num)
                    
                    # Quality check
                    if page_result.quality_score >= self.quality_threshold:
                        pages.append(page_result)
                        extraction_stats["pdfplumber"] += 1
                    else:
                        # Fallback to PyMuPDF + OCR
                        fallback_result = self._extract_page_fallback(pdf_path, page_num)
                        pages.append(fallback_result)
                        extraction_stats[fallback_result.extraction_method] += 1
                    
                    extraction_stats["total_words"] += len(pages[-1].word_boxes)
                    
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {e}")
            # Full PyMuPDF fallback
            pages = self._full_pymupdf_extraction(pdf_path)
            extraction_stats = {"pymupdf_fallback": len(pages), "total_words": sum(len(p.word_boxes) for p in pages)}
        
        return DocumentText(
            filename=pdf_path.name,
            total_pages=len(pages),
            pages=pages,
            extraction_stats=extraction_stats,
            processed_at=datetime.now().isoformat()
        )
    
    def _extract_page_pdfplumber(self, page, page_num: int) -> PageText:
        """Extract text using pdfplumber with quality assessment."""
        # Get characters and words with positioning
        chars = page.chars
        words = page.extract_words(x_tolerance=3, y_tolerance=3)
        text = page.extract_text() or ""
        
        # Build word boxes
        word_boxes = []
        for word in words:
            word_box = WordBox(
                text=word["text"],
                x0=word["x0"],
                y0=word["top"],
                x1=word["x1"],
                y1=word["bottom"],
                page_num=page_num,
                confidence=1.0
            )
            word_boxes.append(word_box)
        
        # Calculate quality score
        quality_score = self._calculate_quality(text, chars, words)
        
        return PageText(
            page_num=page_num,
            text=text,
            word_boxes=word_boxes,
            width=page.width,
            height=page.height,
            extraction_method="pdfplumber",
            quality_score=quality_score
        )
    
    def _extract_page_fallback(self, pdf_path: Path, page_num: int) -> PageText:
        """Fallback extraction using PyMuPDF with OCR."""
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        # Try regular text extraction
        text = page.get_text()
        method = "pymupdf"
        
        # If no text, try OCR
        if not text.strip():
            try:
                import pytesseract
                from PIL import Image
                import io
                
                mat = fitz.Matrix(2, 2)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                text = pytesseract.image_to_string(image)
                method = "ocr"
            except Exception as e:
                logger.warning(f"OCR failed: {e}")
                text = ""
        
        # Create simplified word boxes
        words = text.split()
        word_boxes = []
        if words:
            rect = page.rect
            estimated_width = rect.width / max(1, len(words) / max(1, text.count('\n') + 1))
            
            for i, word in enumerate(words):
                x0 = rect.x0 + (i % 10) * estimated_width  # Rough positioning
                y0 = rect.y0 + (i // 10) * 20
                
                word_box = WordBox(
                    text=word,
                    x0=x0,
                    y0=y0,
                    x1=x0 + len(word) * 6,
                    y1=y0 + 12,
                    page_num=page_num,
                    confidence=0.8 if method == "pymupdf" else 0.6
                )
                word_boxes.append(word_box)
        
        doc.close()
        
        return PageText(
            page_num=page_num,
            text=text,
            word_boxes=word_boxes,
            width=page.rect.width,
            height=page.rect.height,
            extraction_method=method,
            quality_score=0.8 if method == "pymupdf" else 0.6
        )
    
    def _full_pymupdf_extraction(self, pdf_path: Path) -> List[PageText]:
        """Full document extraction using only PyMuPDF."""
        doc = fitz.open(pdf_path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Simple word boxes
            words = text.split()
            word_boxes = []
            for i, word in enumerate(words):
                word_box = WordBox(
                    text=word,
                    x0=i * 10,  # Very rough positioning
                    y0=(i // 10) * 15,
                    x1=(i + 1) * 10,
                    y1=((i // 10) + 1) * 15,
                    page_num=page_num
                )
                word_boxes.append(word_box)
            
            page_text = PageText(
                page_num=page_num,
                text=text,
                word_boxes=word_boxes,
                width=page.rect.width,
                height=page.rect.height,
                extraction_method="pymupdf_fallback",
                quality_score=0.7
            )
            pages.append(page_text)
        
        doc.close()
        return pages
    
    def _calculate_quality(self, text: str, chars: List, words: List) -> float:
        """Calculate text extraction quality score."""
        if not text.strip():
            return 0.0
        
        score = 0.5
        
        # Length indicates content
        if len(text) > 100:
            score += 0.2
        
        # Reasonable char-to-word ratio
        if words and chars:
            ratio = len(chars) / len(words)
            if 4 <= ratio <= 8:
                score += 0.1
        
        # Common document terms
        if any(term in text.lower() for term in ["financial", "company", "revenue", "income"]):
            score += 0.1
        
        # Penalize excessive special characters
        special_ratio = sum(1 for c in text if not c.isalnum() and c not in " .,!?-()") / max(1, len(text))
        if special_ratio > 0.1:
            score -= 0.2
        
        return min(1.0, score)


def test_extraction():
    """Test function with hardcoded PDF path."""
    # Hardcoded path - adjust this relative to where you run the script
    pdf_path = Path("../data/raw/ten-k-2023.pdf")
    
    # Check if file exists
    if not pdf_path.exists():
        print(f"❌ PDF file not found at: {pdf_path.absolute()}")
        print("Please make sure the file exists or adjust the path.")
        return
    
    print(f"✅ Found PDF file at: {pdf_path.absolute()}")
    
    # Create extractor with config
    config = {
        "quality_threshold": 0.7
    }
    extractor = OptimizedTextExtractor(config)
    
    try:
        # Extract text
        print("🔄 Starting text extraction...")
        result = extractor.extract_document(pdf_path)
        
        # Print results
        print("\n" + "="*50)
        print("EXTRACTION RESULTS")
        print("="*50)
        print(f"Filename: {result.filename}")
        print(f"Total pages: {result.total_pages}")
        print(f"Processed at: {result.processed_at}")
        print(f"Extraction stats: {result.extraction_stats}")
        
        # Show first page details
        if result.pages:
            first_page = result.pages[0]
            print(f"\nFirst page details:")
            print(f"- Method: {first_page.extraction_method}")
            print(f"- Quality score: {first_page.quality_score:.2f}")
            print(f"- Dimensions: {first_page.width:.1f} x {first_page.height:.1f}")
            print(f"- Word count: {len(first_page.word_boxes)}")
            
            # Show first 500 characters of text
            if first_page.text:
                print(f"\nFirst 500 characters of text:")
                print("-" * 30)
                print(first_page.text[:500])
                if len(first_page.text) > 500:
                    print("...")
            
            # Show first few word boxes
            if first_page.word_boxes:
                print(f"\nFirst 5 word boxes:")
                print("-" * 30)
                for i, word_box in enumerate(first_page.word_boxes[:5]):
                    print(f"{i+1}. '{word_box.text}' at ({word_box.x0:.1f}, {word_box.y0:.1f}) confidence: {word_box.confidence}")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_extraction()