from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.document import AIReport, Citation, Document, DocumentChunk
from app.schemas.document import CitationListRequest, CitationRequest, DocumentOut, SearchRequest
from app.services.ai_service import build_ai_analysis
from app.services.document_service import calc_hash, save_file

router = APIRouter(prefix="/api/v1")
SUPPORTED_EXTENSIONS = {".pdf", ".caj"}
SUPPORTED_CITATION_STYLES = {"apa", "mla", "gbt7714"}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/documents/import", response_model=DocumentOut)
async def import_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename = file.filename or "untitled"
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="only .pdf and .caj are supported")

    content = await file.read()
    file_hash = calc_hash(content)

    exists = db.scalar(select(Document).where(Document.file_hash == file_hash))
    if exists:
        return exists

    saved_path = save_file(settings.storage_path, filename, content)
    text = content[:4000].decode("utf-8", errors="ignore") or "(empty)"

    doc = Document(title=filename, file_path=saved_path, file_hash=file_hash)
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
        select(Document.id, Document.title, DocumentChunk.content, DocumentChunk.page_no)
        .join(DocumentChunk, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.content.ilike(f"%{req.query}%"))
        .limit(20)
    ).all()
    return [
        {
            "document_id": document_id,
            "title": title,
            "snippet": content[:200],
            "page_no": page_no,
        }
        for document_id, title, content, page_no in rows
    ]


@router.post("/ai/analyze/{document_id}")
def analyze_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")

    first_chunk = db.scalar(
        select(DocumentChunk).where(DocumentChunk.document_id == document_id).limit(1)
    )
    source = first_chunk.content if first_chunk else ""
    analysis = build_ai_analysis(source_text=source, title=doc.title)

    report = db.scalar(select(AIReport).where(AIReport.document_id == document_id))
    if report is None:
        report = AIReport(
            document_id=document_id,
            summary=analysis["concise_summary"],
            method=analysis["research_method"],
            findings="\n".join(analysis["core_points"]),
            limitations="Heuristic draft. Replace with real LLM pipeline in production.",
        )
        db.add(report)
    else:
        report.summary = analysis["concise_summary"]
        report.method = analysis["research_method"]
        report.findings = "\n".join(analysis["core_points"])

    db.commit()

    return {
        "document_id": document_id,
        **analysis,
    }


@router.post("/ai/summarize/{document_id}")
def summarize(document_id: int, db: Session = Depends(get_db)):
    analysis = analyze_document(document_id=document_id, db=db)
    return {
        "document_id": analysis["document_id"],
        "summary": analysis["concise_summary"],
        "method": analysis["research_method"],
        "findings": "\n".join(analysis["core_points"]),
        "limitations": "Heuristic draft. Replace with real LLM pipeline in production.",
    }


def _format_citation(style: str, title: str) -> str:
    if style == "apa":
        return f"{title}. (n.d.). AcaLite Local Library."
    if style == "mla":
        return f'"{title}." AcaLite Local Library, n.d., acalite.local.'
    return f"{title}[J]. AcaLite Local Library, n.d."


@router.post("/citations/generate")
def generate_citation(req: CitationRequest, db: Session = Depends(get_db)):
    doc = db.get(Document, req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document not found")

    style = req.style.lower()
    if style not in SUPPORTED_CITATION_STYLES:
        raise HTTPException(status_code=400, detail="style must be apa, mla or gbt7714")

    formatted = _format_citation(style, doc.title)

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


@router.post("/citations/generate-list")
def generate_citation_list(req: CitationListRequest, db: Session = Depends(get_db)):
    style = req.style.lower()
    if style not in SUPPORTED_CITATION_STYLES:
        raise HTTPException(status_code=400, detail="style must be apa, mla or gbt7714")

    if not req.document_ids:
        raise HTTPException(status_code=400, detail="document_ids cannot be empty")

    docs = (
        db.execute(select(Document).where(Document.id.in_(req.document_ids)).order_by(Document.id.asc()))
        .scalars()
        .all()
    )
    if not docs:
        raise HTTPException(status_code=404, detail="documents not found")

    references = []
    for doc in docs:
        formatted = _format_citation(style, doc.title)
        references.append(formatted)
        citation = Citation(
            document_id=doc.id,
            style=style,
            formatted_text=formatted,
            bibtex="",
        )
        db.add(citation)

    db.commit()
    return {
        "style": style,
        "count": len(references),
        "references": references,
        "reference_list": "\n".join(f"[{i + 1}] {ref}" for i, ref in enumerate(references)),
    }
