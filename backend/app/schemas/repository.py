from pydantic import BaseModel, HttpUrl


class RepositoryCreate(BaseModel):
    url: HttpUrl
    name: str
    description: str | None = None


class RepositoryResponse(BaseModel):
    id: int
    url: str
    name: str
    description: str | None = None

    class Config:
        from_attributes = True