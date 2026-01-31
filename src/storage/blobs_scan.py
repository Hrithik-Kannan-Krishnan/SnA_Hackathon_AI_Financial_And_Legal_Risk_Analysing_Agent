"""Scanning blob storage for deal files"""
from pathlib import Path
from typing import List, Dict, Any


def list_deal_files(deal_id: str, storage_root: str = "storage") -> List[Dict[str, Any]]:
    """List all files for a specific deal"""
    storage_path = Path(storage_root) / "blobs" / deal_id
    
    if not storage_path.exists():
        return []
    
    files = []
    for file_path in storage_path.iterdir():
        if file_path.is_file():
            # Parse the stored filename format: {doc_id}_{original_name}
            filename = file_path.name
            if '_' in filename:
                doc_id, original_name = filename.split('_', 1)
            else:
                doc_id = filename[:8]  # fallback
                original_name = filename
            
            files.append({
                "doc_id": doc_id,
                "original_name": original_name,
                "stored_path": str(file_path),
                "size_bytes": file_path.stat().st_size
            })
    
    return files
