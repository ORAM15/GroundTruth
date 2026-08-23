from __future__ import annotations

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(50))
    source_uri: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    versions: Mapped[list["DocumentVersionRow"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentVersionRow(Base):
    __tablename__ = "document_versions"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    version_label: Mapped[str] = mapped_column(String(100))
    source_uri: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_until: Mapped[date | None] = mapped_column(Date)
    document: Mapped[DocumentRow] = relationship(back_populates="versions")
    chunks: Mapped[list["ChunkRow"]] = relationship(back_populates="version", cascade="all, delete-orphan")


class ChunkRow(Base):
    __tablename__ = "chunks"
    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id"), index=True)
    section_id: Mapped[str | None] = mapped_column(String(128), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    canonical_embedding_text: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    source_span: Mapped[dict] = mapped_column(JSON, default=dict)
    structural_path: Mapped[list] = mapped_column(JSON, default=list)
    representation_version: Mapped[str] = mapped_column(String(50), default="REP-01")
    version: Mapped[DocumentVersionRow] = relationship(back_populates="chunks")


class ChunkEmbeddingRow(Base):
    __tablename__ = "chunk_embeddings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunks.id"), index=True)
    model_provider: Mapped[str] = mapped_column(String(100))
    model_name: Mapped[str] = mapped_column(String(200))
    model_version: Mapped[str | None] = mapped_column(String(200))
    representation_version: Mapped[str] = mapped_column(String(50))
    dimensions: Mapped[int] = mapped_column(Integer)
    vector: Mapped[list[float]] = mapped_column(Vector())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def create_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine), engine
