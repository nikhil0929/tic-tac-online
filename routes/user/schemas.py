from pydantic import BaseModel, Field


class CreateUserRequest(BaseModel):
    first_name: str = Field(..., description="First name of the user")
    last_name: str = Field(..., description="Last name of the user")
    username: str = Field(..., description="Username of the user")
    password: str = Field(..., description="Password of the user")


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username of the user")
    password: str = Field(..., description="Password of the user")


class Token(BaseModel):
    access_token: str = Field(..., description="Access token for the user")
    token_type: str = Field(..., description="Type of the token")
    id: int = Field(..., description="ID of the user")


class TokenData(BaseModel):
    username: str = Field(..., description="Username of the user")
    id: int = Field(..., description="ID of the user")
