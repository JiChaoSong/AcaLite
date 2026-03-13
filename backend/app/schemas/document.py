from pydantic import BaseModel, Field


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


class CitationListRequest(BaseModel):
    document_ids: list[int] = Field(default_factory=list)
    style: str = "apa"
