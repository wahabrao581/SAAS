from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ProviderKind = Literal[
    "video_generation",
    "payment",
    "storage",
    "other",
]


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_name: str
    provider_type: ProviderKind
    base_url: str | None = None
    api_key_env: str | None = None
    is_active: bool
    settings: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=150)
    provider_type: ProviderKind = "other"
    base_url: str | None = None
    api_key_env: str | None = Field(default=None, max_length=100)
    is_active: bool = True
    settings: dict = Field(default_factory=dict)


class ProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = Field(default=None, min_length=1, max_length=150)
    provider_type: ProviderKind | None = None
    base_url: str | None = None
    api_key_env: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    settings: dict | None = None


class ProviderModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    provider_id: UUID
    name: str
    display_name: str
    description: str | None = None
    capabilities: dict = Field(default_factory=dict)
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProviderModelCreate(BaseModel):
    provider_id: UUID
    name: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    capabilities: dict = Field(default_factory=dict)
    is_active: bool = True


class ProviderModelUpdate(BaseModel):
    provider_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=100)
    display_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    capabilities: dict | None = None
    is_active: bool | None = None

