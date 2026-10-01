from pydantic import BaseModel, ConfigDict, HttpUrl


class RepositoryCreate(BaseModel):
    url: HttpUrl
    name: str
    description: str | None = None


class RepositoryResponse(BaseModel):
    id: int
    url: str
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)