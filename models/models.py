from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum


class Source(str, Enum):
    catalog = "catalog"


class DocumentMetadata(BaseModel):
    slug: Optional[str] = None
    source: Optional[Source] = "catalog"


class DatasetMetadata(DocumentMetadata):
    geography: Optional[List[Dict[str, str]]] = None
    category: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None
    license: Optional[str] = None
    update_frequency: Optional[str] = None
    spatial_aggregation: Optional[str] = None
    temporal_aggregation: Optional[str] = None
    placetype: Optional[str] = None
    variables: List[Dict[str, str]] = list()


class VariableMetadata(DocumentMetadata):
    column_name: Optional[str] = None
    db_type: Optional[str] = None
    dataset_id: Optional[List[Dict[str, str]]] = None


class DatasetChunkMetadata(DatasetMetadata):
    document_id: Optional[str] = None


class VariableChunkMetadata(VariableMetadata):
    document_id: Optional[str] = None


class DocumentChunk(BaseModel):
    id: Optional[str] = None
    text: str
    metadata: DatasetChunkMetadata | VariableChunkMetadata
    embedding: Optional[List[float]] = None

    class Config:
        smart_union = True


class DocumentChunkWithScore(DocumentChunk):
    score: float


class Document(BaseModel):
    id: str
    text: str
    metadata: Optional[DocumentMetadata] = None


class DocumentWithChunks(Document):
    chunks: List[DocumentChunk]


class DocumentMetadataFilter(BaseModel):
    document_id: Optional[str] = None
    source: Optional[Source] = None
    slug: Optional[str] = None


class DatasetMetadataFilter(DocumentMetadataFilter):
    category: Optional[str] = None
    country: Optional[str] = None
    provider: Optional[str] = None
    license: Optional[str] = None
    update_frequency: Optional[str] = None
    spatial_aggregation: Optional[str] = None
    temporal_aggregation: Optional[str] = None
    placetype: Optional[str] = None


class VariableMetadataFilter(DocumentMetadataFilter):
    column_name: Optional[str] = None
    db_type: Optional[str] = None


class Query(BaseModel):
    query: str
    filter: Optional[DocumentMetadataFilter] = None
    top_k: Optional[int] = 3


class QueryWithEmbedding(Query):
    embedding: List[float]


class QueryResult(BaseModel):
    query: str
    results: List[DocumentChunkWithScore]
