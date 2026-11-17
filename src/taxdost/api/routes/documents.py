from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from taxdost.api.deps import StoreDep

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(
    store: StoreDep,
    q: Annotated[str | None, Query(max_length=200)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    rows = store.search(q)
    return {
        "total": len(rows),
        "limit": limit,
        "offset": offset,
        "items": rows[offset : offset + limit],
    }


@router.get("/{doc_id}")
def get_document(doc_id: str, store: StoreDep) -> dict:
    record = store.get(doc_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"No document with id '{doc_id}'.")
    return record
