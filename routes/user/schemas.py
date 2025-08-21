from pydantic import BaseModel


class Test1Request(BaseModel):
    name: str
