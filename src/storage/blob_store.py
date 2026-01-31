"""Blob storage management for uploaded files"""
import os
import uuid
from pathlib import Path
from typing import NamedTuple


class StoredFile(NamedTuple):
    """Information about a stored file"""
    doc_id: str
    deal_id: str
    original_name: str
    stored_path: Path
    size_bytes: int


def save_upload_bytes(root: Path, deal_id: str, original_name: str, content: bytes) -> StoredFile:
    """Save uploaded file bytes to storage and return metadata"""
    doc_id = str(uuid.uuid4())[:8]
    
    # Create the storage path: root/blobs/deal_id/
    deal_dir = root / "blobs" / deal_id
    deal_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename to avoid conflicts
    file_ext = Path(original_name).suffix
    stored_filename = f"{doc_id}_{original_name}"
    stored_path = deal_dir / stored_filename
    
    # Write the content
    with open(stored_path, 'wb') as f:
        f.write(content)
    
    return StoredFile(
        doc_id=doc_id,
        deal_id=deal_id,
        original_name=original_name,
        stored_path=stored_path,
        size_bytes=len(content)
    )
