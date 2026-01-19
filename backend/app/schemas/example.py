from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExampleBase(BaseModel):
    name: str
    description: str | None = None


class ExampleCreate(ExampleBase):
    pass


class ExampleResponse(ExampleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
