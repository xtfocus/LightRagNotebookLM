import uuid
import datetime
from typing import Optional, List, Dict, Any
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, JSON
from sqlalchemy import Column, UniqueConstraint

#

# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    is_approved: bool = False  # New field for admin approval
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)
    is_approved: bool = Field(default=False)  # Allow setting approval status during creation


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)
    is_approved: bool | None = Field(default=None)  # Allow admins to update approval status


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    documents: list["Document"] = Relationship(back_populates="owner", cascade_delete=True)
    sources: list["Source"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# Core models only. Business-specific domain models have been removed for the template.

# Document Processing Pipeline Models

import enum
from datetime import datetime
from typing import Optional, Dict, Any


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


# Shared properties
class DocumentBase(SQLModel):
    filename: str = Field(max_length=255)
    mime_type: str = Field(max_length=100)
    size: int = Field(ge=0)
    bucket: str = Field(max_length=100)
    object_key: str = Field(max_length=500)
    document_metadata: str = Field(default="{}", max_length=10000)  # JSON string
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    version: int = Field(default=1, ge=1)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)


# Properties to receive via API on creation
class DocumentCreate(DocumentBase):
    pass


# Properties to receive via API on update
class DocumentUpdate(SQLModel):
    filename: Optional[str] = Field(default=None, max_length=255)
    mime_type: Optional[str] = Field(default=None, max_length=100)
    size: Optional[int] = Field(default=None, ge=0)
    bucket: Optional[str] = Field(default=None, max_length=100)
    object_key: Optional[str] = Field(default=None, max_length=500)
    document_metadata: Optional[str] = Field(default=None, max_length=10000)
    status: Optional[ProcessingStatus] = Field(default=None)
    version: Optional[int] = Field(default=None, ge=1)


# Database model
class Document(DocumentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner: User | None = Relationship(back_populates="documents")
    source_id: Optional[uuid.UUID] = Field(default=None, foreign_key="source.id")
    source: Optional["Source"] = Relationship(back_populates="document")
    
    # Add unique constraint for idempotency
    __table_args__ = (
        UniqueConstraint('owner_id', 'object_key', name='uq_user_object_key'),
    )


# Properties to return via API
class DocumentPublic(DocumentBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentsPublic(SQLModel):
    data: list[DocumentPublic]
    count: int


# Source Models for URL Processing

class SourceType(str, enum.Enum):
    DOCUMENT = "document"    # Links to existing Document
    URL = "url"             # Web pages, articles
    VIDEO = "video"         # Video files or YouTube links
    IMAGE = "image"         # Image files
    TEXT = "text"           # Direct text input


# Shared properties for Source
class SourceBase(SQLModel):
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    source_type: SourceType
    source_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)


# Database model for Source
class Source(SourceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    owner: User | None = Relationship(back_populates="sources")
    document: Optional["Document"] = Relationship(back_populates="source")


# Properties to return via API
class SourcePublic(SourceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SourcesPublic(SQLModel):
    data: list[SourcePublic]
    count: int


# Search Results
class SearchResult(SQLModel):
    document_id: uuid.UUID
    filename: str
    score: float
    chunk_text: str
    chunk_index: int
    doc_metadata: Dict[str, Any] = Field(alias="metadata")


class SearchResults(SQLModel):
    results: list[SearchResult]
    total: int
    query: str


# Event Schema for Kafka
class DocumentEvent(SQLModel):
    op: str = Field(description="Operation: 'c'=create, 'u'=update, 'd'=delete")
    ts_ms: int = Field(description="Timestamp in milliseconds")
    document_id: uuid.UUID
    version: int
    doc_metadata: Dict[str, Any] = Field(alias="metadata")
    owner_id: uuid.UUID


# URL Source Event Schema for Kafka
class URLSourceEvent(SQLModel):
    op: str = Field(description="Operation: 'c'=create, 'u'=update, 'd'=delete")
    ts_ms: int = Field(description="Timestamp in milliseconds")
    source_id: uuid.UUID
    version: int
    source_metadata: Dict[str, Any] = Field(alias="metadata")
    owner_id: uuid.UUID
