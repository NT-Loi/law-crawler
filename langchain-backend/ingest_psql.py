from sqlmodel import Field, SQLModel, Relationship, create_engine, UniqueConstraint
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv
from typing import Optional, List
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_engine(DATABASE_URL, echo=DB_ECHO)
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=DB_ECHO)
async_session_factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

class PDNode(SQLModel, table=True):
    __tablename__ = "pd_nodes"
    id: str = Field(primary_key=True)
    content: str
    title: str = Field(index=True)
    demuc_id: Optional[str] = Field(default=None, index=True)
    references: List["PDReference"] = Relationship(back_populates="pd_node")


class VBQPPLDoc(SQLModel, table=True):
    __tablename__ = "vbqppl_docs"
    id: str = Field(primary_key=True)
    doc_number: Optional[str] = Field(default=None, index=True)
    doc_date: Optional[datetime] = Field(default=None)
    title: Optional[str] = Field(default=None, index=True)
    url: str
    is_crawled: bool = Field(default=False)
    
    nodes: List["VBQPPLNode"] = Relationship(back_populates="doc")


class VBQPPLNode(SQLModel, table=True):
    __tablename__ = "vbqppl_nodes"
    id: Optional[int] = Field(default=None, primary_key=True) # MAPC
    doc_id: str = Field(foreign_key="vbqppl_docs.id", index=True)
    label: str = Field(index=True)
    content: str
    parent_id: Optional[int] = Field(default=None, foreign_key="vbqppl_nodes.id")
    parents_label: Optional[str] = Field(default=None) 
    doc: VBQPPLDoc = Relationship(back_populates="nodes")


class PDReference(SQLModel, table=True):
    __tablename__ = "pd_references"
    id: Optional[int] = Field(default=None, primary_key=True)
    phapdien_id: str = Field(foreign_key="phapdien_nodes.id", index=True)
    vbqppl_doc_id: str = Field(foreign_key="vbqppl_docs.id")
    vbqppl_label: str = Field(index=True)
    details: str
    phapdien_node: PhapDienNode = Relationship(back_populates="references")


class PhapDienRelation(SQLModel, table=True):
    __tablename__ = "phapdien_relations"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", name="unique_relation_pair"),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: str = Field(foreign_key="phapdien_nodes.id", index=True)
    target_id: str = Field(foreign_key="phapdien_nodes.id", index=True)


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"
    id: str = Field(primary_key=True)
    title: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    
    messages: List["ChatMessage"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    user_docs: List["UserDocument"] = Relationship(back_populates="session", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="chat_sessions.id", index=True)
    role: str # 'user' or 'assistant'
    content: str
    sources: Optional[str] = Field(default=None) # JSON-stringified sources
    created_at: datetime = Field(default_factory=datetime.now)
    
    session: ChatSession = Relationship(back_populates="messages")


class UserDocument(SQLModel, table=True):
    __tablename__ = "user_documents"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="chat_sessions.id", index=True)
    filename: str
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    session: ChatSession = Relationship(back_populates="user_docs")


def init_db(drop_all: bool = False):
    if drop_all:
        print("Dropping all tables...")
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


async def get_async_session():
    async with async_session_factory() as session:
        yield session