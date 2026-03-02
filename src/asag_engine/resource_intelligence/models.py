from sqlalchemy import Column, String, Integer, Text, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ResourceChunk(Base):
    __tablename__ = "resource_chunks"

    chunk_id = Column(String, primary_key=True)
    doc_id = Column(String, index=True)
    filename = Column(String)
    file_type = Column(String)
    page_number = Column(Integer)
    chunk_text = Column(Text)
    snippet = Column(Text)