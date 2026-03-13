from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    title: str
    file_path: str

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str


class CitationRequest(BaseModel):
    document_id: int
    style: str = "apa"
