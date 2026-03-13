from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db
from app.core.config import settings
from app.models.document import AIReport, Citation, Document, DocumentChunk
from app.schemas.document import CitationRequest, DocumentOut, SearchRequest
from app.services.document_service import calc_hash, save_file

router = APIRouter(prefix="/api/v1")


@router.on_event("startup")
def startup_create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/documents/import", response_model=DocumentOut)
async def import_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    file_hash = calc_hash(content)

    exists = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if exists:
        return exists

    saved_path = save_file(settings.storage_path, file.filename, content)
    text = content[:2000].decode("utf-8", errors="ignore") or "(empty)"

    doc = Document(title=file.filename, file_path=saved_path, file_hash=file_hash)
    db.add(doc)
    db.flush()

    chunk = DocumentChunk(document_id=doc.id, chunk_index=0, content=text, page_no=1)
    db.add(chunk)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/retrieval/search")
def search(req: SearchRequest, db: Session = Depends(get_db)):
    rows = db.execute(
        select(Document.title, DocumentChunk.content, DocumentChunk.page_no)
        .join(DocumentChunk, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.content.ilike(f"%{req.query}%"))
        .limit(20)
    ).all()
    return [
        {"title": title, "snippet": content[:200], "page_no": page_no}
        for title, content, page_no in rows
    ]


@router.post("/ai/summarize/{document_id}")
def summarize(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")

    first_chunk = db.scalar(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).limit(1)
    )
    source = first_chunk.content if first_chunk else ""
    summary = (source[:280] + "...") if len(source) > 280 else source

    report = db.scalar(select(AIReport).where(AIReport.document_id == document_id))
    if report is None:
        report = AIReport(
            document_id=document_id,
            summary=summary,
            method="TBD",
            findings="TBD",
            limitations="TBD",
        )
        db.add(report)
    else:
        report.summary = summary

    db.commit()
    return {
        "document_id": document_id,
        "summary": report.summary,
        "method": report.method,
        "findings": report.findings,
        "limitations": report.limitations,
    }


@router.post("/citations/generate")
def generate_citation(req: CitationRequest, db: Session = Depends(get_db)):
    doc = db.get(Document, req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")

    style = req.style.lower()
    if style not in {"apa", "gbt7714"}:
        raise HTTPException(status_code=400, detail="style must be apa or gbt7714")

    if style == "apa":
        formatted = f"{doc.title}. (n.d.). AcaLite Local Library."
    else:
        formatted = f"{doc.title}[J]. AcaLite Local Library, n.d."

    bibtex = (
        f"@misc{{doc_{doc.id},\n"
        f"  title={{ {doc.title} }},\n"
        f"  howpublished={{AcaLite Local Library}},\n"
        f"  year={{n.d.}}\n"
        f"}}"
    )

    citation = Citation(
        document_id=doc.id,
        style=style,
        formatted_text=formatted,
        bibtex=bibtex,
    )
    db.add(citation)
    db.commit()

    return {"style": style, "formatted_text": formatted, "bibtex": bibtex}
