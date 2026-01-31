"""Utilities for unpacking ZIP files"""
import zipfile
from pathlib import Path
from typing import List, Dict, Any


def unpack_zip(zip_path: str, extract_to: str) -> List[Dict[str, Any]]:
    """Unpack a ZIP file and return list of extracted files"""
    extracted_files = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.infolist():
            if not file_info.is_dir():
                extracted_path = zip_ref.extract(file_info, extract_to)
                extracted_files.append({
                    "original_name": file_info.filename,
                    "extracted_path": extracted_path,
                    "size": file_info.file_size
                })
    
    return extracted_files
