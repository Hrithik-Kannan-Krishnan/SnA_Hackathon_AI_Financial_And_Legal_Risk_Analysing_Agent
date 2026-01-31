"""Document indexing for deals"""
from typing import List, Dict, Any
import sqlite3
from pathlib import Path


def list_docs_for_deal(deal_id: str, db_path: str = "./storage/sqlite/app.db") -> List[Dict[str, Any]]:
    """List all documents for a specific deal from the database"""
    docs = []
    
    # Ensure database directory exists
    db_path_obj = Path(db_path)
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                deal_id TEXT,
                filename TEXT,
                stored_path TEXT,
                doc_type TEXT,
                router_rationale TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Fetch documents for the deal
        cursor.execute("""
            SELECT doc_id, deal_id, filename, stored_path, doc_type, router_rationale, created_at
            FROM documents 
            WHERE deal_id = ?
            ORDER BY created_at DESC
        """, (deal_id,))
        
        rows = cursor.fetchall()
        for row in rows:
            docs.append({
                "doc_id": row[0],
                "deal_id": row[1],
                "filename": row[2],
                "stored_path": row[3],
                "doc_type": row[4],
                "router_rationale": row[5],
                "created_at": row[6]
            })
        
        conn.close()
    except Exception as e:
        print(f"Error accessing database: {e}")
    
    return docs
