from enum import Enum
import os
from pathlib import Path
import re
from typing import List, Optional
import uuid

from docx import Document
from pypdf import PdfReader

from app.core.exceptions import ErrorCode, ValidationError
from app.core.logging import logger

from pathlib import Path

TEMP_FOLDER = Path("/tmp")
TEMP_FOLDER.mkdir(exist_ok=True)


class FileExtension(Enum):
    PNG = "png"
    JPG= "jpg"
    JPEG= "jpeg"
    MP4 = "mp4"
    EPUB = "epub"
    PDF = "pdf"
    DOCX = "docx"
    
    
class FileContentType(Enum):
    PNG = "image/png"
    JPG = "image/jpeg"
    MP4 = "video/mp4"
    EPUB = "application/epub+zip"
    PDF = "application/pdf"
    APPLICATION_OCTET_STREAM = "application/octet-stream"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def sanitize_filename(filename: str) -> str:
    """Remove leading or trailing spaces, replace spaces with underscores and remove special characters from filename.

    Args:
        filename (str): Name of file

    Returns:
        str: Sanitized file name.
    """
    filename = filename.strip()  # Remove leading/trailing spaces
    filename = filename.replace(" ", "_")  # Replace spaces with underscores
    filename = re.sub(r"[^a-zA-Z0-9_.-]", "", filename)  # Remove special characters
    return filename


def convert_from_bytes_to_mb(size: float)->float:
    """Convert from bytes to megabytes. Result is size/1000000 rounded to 2 decimal places

    Args:
        size (float): Float in bytes. 

    Returns:
        float: Size in megabytes rounded to two.
    """
    conversion_factor = 1000000
    return round((size/conversion_factor), 2)
            
    
def get_file_extension(filename) -> str:
    name, extension = os.path.splitext(filename)
    extension = extension[1:].lower()
    return extension
    
    
def get_file_content_type(filename: str) -> Optional[str]:
    """Get file content type using extension in the filename

    Args:
        filename (str): 

    Returns:
        Optional[str]: File content type or none if the extracted extension is not mp4, jpg, jpeg, png, epub or pdf.
    """
    
    content_type = None
    
    extension = get_file_extension(filename)
    
    if extension.lower() == FileExtension.MP4.value:
        content_type = FileContentType.MP4.value
        
    if extension.lower() == FileExtension.JPEG.value or extension.lower() == FileExtension.JPG.value:
        content_type = FileContentType.JPG.value
        
    if extension.lower() == FileExtension.PNG.value:
        content_type = FileContentType.PNG.value  
        
    if extension.lower() == FileExtension.EPUB.value:
        content_type = FileContentType.EPUB.value
        
    if extension.lower() == FileExtension.PDF.value:
        content_type = FileContentType.PDF.value
    
    if extension.lower() == FileExtension.DOCX.value:
        content_type = FileContentType.DOCX.value
        
    return content_type
    
    
def generate_unique_filename(filename: str) -> str:
    """Use uuid.uuid4 method to generate unique filename

    Args:
        filename (str): Filename including extension.

    Returns:
        str: A string of the format "{unique_id}.{extension}"
    """
    unique_id = str(uuid.uuid4())
    extension = get_file_extension(filename)
    return f"{unique_id}.{extension}"


def validate_file_extension(
    filename: str, 
    allowed_extensions: List[str]
) -> None:
    """Validates the file extension by checking if the extension in the filename is in allowed_extensions

    Args:
        filename (str): filename (including extension)
        allowed_extensions (List[str]): Allowed extensions.

    Raises:
        ValidationError: If extension in filename is not in allowed_extensions.
    """
    
    from app.utils.file import get_file_extension

    extension = get_file_extension(filename)
    if extension not in allowed_extensions:
        raise ValidationError(
            error_code=ErrorCode.UNSUPPORTED_FILE_TYPE.value,
            message=f"Allowed extensions are: {', '.join(allowed_extensions)}."
        )
        
        
def extract_pdf_text(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from pdf: {str(e)}")
        raise


def extract_docx_text(file_path: str) -> str:
    try:
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting text from docx: {str(e)}")
        raise


def extract_text(
    extension: str,
    file_path: str
) -> str:
    if extension == FileExtension.DOCX.value:
        return extract_docx_text(file_path)
    elif extension == FileExtension.PDF.value:
        return extract_pdf_text(file_path)
    else:
        logger.error(f"Invalid extension: {extension}")
        raise ValidationError(message=f"Invalid extension: {extension}")