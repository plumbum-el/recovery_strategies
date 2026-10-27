
from pydantic import BaseModel, ConfigDict, Field


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    short_description: str | None = None
    status: str
    image_url: str | None = None
    video_url: str | None = None
    estimated_time: int | None = None
    cost: int | None = None
    creator_id: int
    is_creator: int = 0
    is_liked: int = 0
    likes_count: int = 0


class PublishRequest(BaseModel):
    estimated_time: int = Field(ge=0)
    cost: int = Field(ge=0)
    short_description: str | None = None


class LikeRequest(BaseModel):
    liked: int = Field(ge=0, le=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    username: str
    password: str
