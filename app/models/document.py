"""Document model - SQLAlchemy ORM"""
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    chunks_count = Column(Integer, default=0)
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False
    )

    # Relationship: One document has many chat history entries
    chat_history = relationship(
        "ChatHistory",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status.value}')>"
