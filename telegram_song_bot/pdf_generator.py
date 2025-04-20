"""
PDF Generator module for creating PDF files from song lyrics.

This module provides functionality to create PDF files with lyrics,
automatically adjusting the font size to fit content on a single page.
"""
from fpdf import FPDF
import os
from typing import Optional


class LyricsPDFGenerator:
    """
    Creates PDF documents containing song lyrics with optimized font size.
    
    This class handles the creation of PDF files, with automatic font size
    adjustment to try to fit the lyrics on a single page.
    """
    
    def __init__(self, 
                 margins: int = 4, 
                 min_font_size: int = 6,
                 font_name: str = 'DejaVu',
                 font_path: str = "DejaVuSans.ttf"):
        """
        Initialize the PDF generator with default settings.
        
        Args:
            margins: Page margins in mm
            min_font_size: Minimum allowed font size in points
            font_name: Name of the font to use
            font_path: Path to the font file
        """
        self.margins = margins
        self.min_font_size = min_font_size
        self.font_name = font_name
        self.font_path = font_path
    
    def _create_pdf_with_font_size(self, text: str, font_size: float) -> FPDF:
        """
        Create a PDF document with the given font size.
        
        Args:
            text: Text to include in the PDF
            font_size: Font size to use
            
        Returns:
            FPDF object with the formatted text
        """
        pdf = FPDF()
        pdf.set_margins(left=self.margins, top=self.margins, right=self.margins)
        pdf.set_auto_page_break(auto=True, margin=self.margins)
        pdf.add_page()
        pdf.add_font(self.font_name, '', self.font_path, uni=True)
        pdf.set_font(self.font_name, '', size=font_size)
        
        # Calculate line height based on font size
        line_height = font_size / 2.5
        pdf.multi_cell(0, line_height, text, align="L")
        
        return pdf
    
    def _check_fits_on_page(self, text: str, font_size: float) -> bool:
        """
        Check if the text fits on a single page with the given font size.
        
        Args:
            text: Text to check
            font_size: Font size to use
            
        Returns:
            True if the text fits on a single page, False otherwise
        """
        temp_pdf_path = "temp_check.pdf"
        
        # Create and save a temporary PDF
        test_pdf = self._create_pdf_with_font_size(text, font_size)
        test_pdf.output(temp_pdf_path)
        
        # Check if it fits on one page
        fits_on_page = test_pdf.page_no() == 1
        
        # Clean up temporary file
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            
        return fits_on_page
    
    def _find_optimal_font_size(self, text: str) -> float:
        """
        Find the optimal font size to fit the text on a single page.
        
        Args:
            text: Text to optimize for
            
        Returns:
            Optimal font size
        """
        # Start with a generous font size
        font_size = 30
        
        # Binary search would be more efficient, but this approach
        # is simpler and still performs well for this use case
        while font_size > self.min_font_size:
            if self._check_fits_on_page(text, font_size):
                break
            # Gradually decrease font size
            font_size -= 0.5
        
        return max(font_size, self.min_font_size)
    
    def create_pdf(self, text: str, output_path: str) -> str:
        """
        Create a PDF document with text formatted to fit on a single page.
        
        Args:
            text: Text to include in the PDF
            output_path: Path where to save the PDF file
            
        Returns:
            Path to the created PDF file
        """
        # Find optimal font size
        font_size = self._find_optimal_font_size(text)
        
        # Create PDF with the optimal font size
        pdf = self._create_pdf_with_font_size(text, font_size)
        
        # Check if the content still doesn't fit on one page
        page_count = pdf.page_no()
        if page_count > 1:
            print(f"Warning: Content required {page_count} pages even with minimum font size.")
        
        # Save the PDF file
        pdf.output(output_path)
        print(f"Created PDF with font size {font_size}pt at: {output_path}")
        
        return output_path


def create_pdf(lyrics: str, output_path: str) -> str:
    """
    Create a PDF document containing song lyrics, optimizing font size.
    
    This is a convenience function that uses LyricsPDFGenerator internally.
    
    Args:
        lyrics: String containing the song lyrics
        output_path: Path where to save the PDF file
    
    Returns:
        The path to the created PDF file
    """
    generator = LyricsPDFGenerator()
    return generator.create_pdf(lyrics, output_path)