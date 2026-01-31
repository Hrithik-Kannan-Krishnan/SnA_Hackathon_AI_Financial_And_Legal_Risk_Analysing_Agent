import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import uuid
import shutil

from src.db.deals_store import load_deals
try:
    from src.db.deals_store import save_deal
except Exception:
    from src.db.deals_store import save_deals
    def save_deal(deal: dict) -> None:
        deals = load_deals()
        did = deal.get('deal_id')
        for i,d in enumerate(deals):
            if d.get('deal_id') == did:
                deals[i] = {**d, **deal}
                save_deals(deals)
                return
        deals.append(deal)
        save_deals(deals)

from src.storage.docs_index import list_docs_for_deal

st.set_page_config(page_title="Demo Mode", layout="wide")
st.title("Demo Mode")

st.caption("Creates a new deal and copies selected PDFs from existing blob storage into it.")

deals = load_deals()
all_deal_ids = [d["deal_id"] for d in deals]

src_deal = st.selectbox("Copy documents from deal", all_deal_ids if all_deal_ids else ["(none)"])
if src_deal != "(none)":
    docs = list_docs_for_deal(src_deal)
else:
    docs = []

st.write(f"Source deal has **{len(docs)}** files.")
choices = st.multiselect("Select files to copy", [d["filename"] for d in docs])

new_name = st.text_input("New deal name", value="Demo Deal (Preloaded)")
if st.button("Create new deal + copy files"):
    if not choices:
        st.error("Pick at least 1 file.")
        st.stop()
    new_id = str(uuid.uuid4())[:8]
    save_deal({"deal_id": new_id, "deal_name": new_name})

    for d in docs:
        if d["filename"] not in choices:
            continue
        src_path = Path(d["path"])
        dst_dir = Path("storage/blobs") / new_id / d["doc_id"]
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_dir / src_path.name)

    st.success(f"Created deal {new_name} ({new_id}) and copied {len(choices)} file(s).")
    st.info("Next: go Home → select this deal → Ingest into RAG → Run Agents.")
