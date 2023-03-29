# TODO
import asyncio
from typing import Dict, List, Optional
from loguru import logger
from weaviate import Client
import weaviate
import os
import uuid

from weaviate.util import generate_uuid5

from datastore.datastore import DataStore
from datastore.schema.weaviate_schema import schema as datastore_schema

from models.models import (
    DocumentChunk,
    DatasetChunkMetadata,
    DocumentMetadataFilter,
    QueryResult,
    QueryWithEmbedding,
    DocumentChunkWithScore,
)


WEAVIATE_HOST = os.environ.get("WEAVIATE_HOST", "http://127.0.0.1")
WEAVIATE_PORT = os.environ.get("WEAVIATE_PORT", "8080")
WEAVIATE_USERNAME = os.environ.get("WEAVIATE_USERNAME", None)
WEAVIATE_PASSWORD = os.environ.get("WEAVIATE_PASSWORD", None)
WEAVIATE_SCOPES = os.environ.get("WEAVIATE_SCOPE", None)

WEAVIATE_BATCH_SIZE = int(os.environ.get("WEAVIATE_BATCH_SIZE", 20))
WEAVIATE_BATCH_DYNAMIC = os.environ.get("WEAVIATE_BATCH_DYNAMIC", False)
WEAVIATE_BATCH_TIMEOUT_RETRIES = int(os.environ.get("WEAVIATE_TIMEOUT_RETRIES", 3))
WEAVIATE_BATCH_NUM_WORKERS = int(os.environ.get("WEAVIATE_BATCH_NUM_WORKERS", 1))


def extract_schema_properties(schema):
    return {
        schema["class"]: {property["name"] for property in schema["properties"]}
        for schema in schema["classes"]
    }


class WeaviateDataStore(DataStore):
    def handle_errors(self, results: Optional[List[dict]]) -> List[str]:
        if not self or not results:
            return []

        error_messages = []
        for result in results:
            if (
                "result" not in result
                or "errors" not in result["result"]
                or "error" not in result["result"]["errors"]
            ):
                continue
            for message in result["result"]["errors"]["error"]:
                error_messages.append(message["message"])
                logger.exception(message["message"])

        return error_messages

    def __init__(self):
        auth_credentials = self._build_auth_credentials()

        url = f"{WEAVIATE_HOST}:{WEAVIATE_PORT}"

        logger.debug(
            f"Connecting to weaviate instance at {url} with credential type {type(auth_credentials).__name__}"
        )
        self.client = Client(url, auth_client_secret=auth_credentials)
        self.client.batch.configure(
            batch_size=WEAVIATE_BATCH_SIZE,
            dynamic=WEAVIATE_BATCH_DYNAMIC,  # type: ignore
            callback=self.handle_errors,  # type: ignore
            timeout_retries=WEAVIATE_BATCH_TIMEOUT_RETRIES,
            num_workers=WEAVIATE_BATCH_NUM_WORKERS,
        )

        if self.client.schema.contains(datastore_schema):
            current_schema = self.client.schema.get()
            current_schema_properties = extract_schema_properties(current_schema)

            logger.debug(
                f"Found index with properties {current_schema_properties}"
            )
            logger.debug("Will reuse this schema")
        else:
            new_schema_properties = extract_schema_properties(datastore_schema)
            logger.debug(
                f"Creating index with properties {new_schema_properties}"
            )
            self.client.schema.create(datastore_schema)

    @staticmethod
    def _build_auth_credentials():
        if WEAVIATE_USERNAME and WEAVIATE_PASSWORD:
            return weaviate.auth.AuthClientPassword(
                WEAVIATE_USERNAME, WEAVIATE_PASSWORD, WEAVIATE_SCOPES
            )
        else:
            return None

    async def _upsert(self, class_name: str, chunks: Dict[str, List[DocumentChunk]]) -> List[str]:
        """
        Takes in a list of list of document chunks and inserts them into the database.
        Return a list of document ids.
        """
        doc_ids = []

        with self.client.batch as batch:
            for doc_id, doc_chunks in chunks.items():
                logger.debug(f"Upserting {doc_id} with {len(doc_chunks)} chunks")
                assert len(doc_chunks) == 1, "We are not splitting so there should be a single chunk"

                for doc_chunk in doc_chunks:
                    # we generate a uuid regardless of the format of the document_id because
                    # weaviate needs a uuid to store each document chunk and
                    # a document chunk cannot share the same uuid
                    doc_uuid = generate_uuid5(doc_id, class_name)
                    metadata = doc_chunk.metadata
                    doc_chunk_dict = doc_chunk.dict()
                    doc_chunk_dict.pop("metadata")
                    for key, value in metadata.dict().items():
                        doc_chunk_dict[key] = value
                    doc_chunk_dict["chunk_id"] = doc_chunk_dict.pop("id")
                    doc_chunk_dict["source"] = (
                        doc_chunk_dict.pop("source").value
                        if doc_chunk_dict["source"]
                        else None
                    )
                    embedding = doc_chunk_dict.pop("embedding")

                    batch.add_data_object(
                        uuid=doc_uuid,
                        data_object=doc_chunk_dict,
                        class_name=class_name,
                        vector=embedding,
                    )

                    if class_name == "DOVariable":
                        # Update the DODataset to have a reference to the variable
                        batch.add_reference(
                            from_object_class_name="DODataset",
                            from_property_name="variables",
                            from_object_uuid=doc_chunk_dict["dataset_id"][0]["beacon"],
                            to_object_class_name=class_name,
                            to_object_uuid=doc_uuid,
                        )

                doc_ids.append(doc_id)
            batch.flush()
        return doc_ids

    async def _query(
        self,
        class_name: str,
        queries: List[QueryWithEmbedding],
    ) -> List[QueryResult]:
        """
        Takes in a list of queries with embeddings and filters and returns a list of query results with matching document chunks and scores.
        """

        async def _single_query(query: QueryWithEmbedding) -> QueryResult:
            logger.debug(f"Query: {query.query}")
            if not hasattr(query, "filter") or not query.filter:
                result = (
                    self.client.query.get(
                        class_name,
                        [
                            # FIXME: it will break if we change the class_name
                            "chunk_id",
                            "document_id",
                            "text",
                            "slug",
                            "geography",
                            "category",
                            "country",
                            "provider",
                            "license",
                            "update_frequency",
                            "spatial_agg",
                            "temporal_agg",
                            "placetype"
                        ],
                    )
                    .with_hybrid(query=query.query, alpha=0.5, vector=query.embedding)
                    .with_limit(query.top_k)  # type: ignore
                    .with_additional(["score", "vector"])
                    .do()
                )
            else:
                filters_ = self.build_filters(query.filter)
                result = (
                    self.client.query.get(
                        class_name,
                        [
                            # FIXME: it will break if we change the class_name
                            "chunk_id",
                            "document_id",
                            "text",
                            "slug",
                            "geography",
                            "category",
                            "country",
                            "provider",
                            "license",
                            "update_frequency",
                            "spatial_agg",
                            "temporal_agg",
                            "placetype"
                        ],
                    )
                    .with_hybrid(query=query.query, alpha=0.5, vector=query.embedding)
                    .with_where(filters_)
                    .with_limit(query.top_k)  # type: ignore
                    .with_additional(["score", "vector"])
                    .do()
                )

            query_results: List[DocumentChunkWithScore] = []
            response = result["data"]["Get"][class_name]

            for resp in response:
                result = DocumentChunkWithScore(
                    id=resp["chunk_id"],
                    text=resp["text"],
                    embedding=resp["_additional"]["vector"],
                    score=resp["_additional"]["score"],
                    # FIXME: this will crash and burn
                    metadata=DatasetChunkMetadata(
                        document_id=resp["document_id"] if resp["document_id"] else "",
                        slug=resp["slug"] if resp["slug"] else "",
                        geography=resp["geography"] if resp["geography"] else "",
                        category=resp["category"] if resp["category"] else "",
                        country=resp["country"] if resp["country"] else "",
                        provider=resp["provider"] if resp["provider"] else "",
                        license=resp["license"] if resp["license"] else "",
                        update_frequency=resp["update_frequency"] if resp["update_frequency"] else "",
                        spatial_agg=resp["spatial_agg"] if resp["spatial_agg"] else "",
                        temporal_agg=resp["temporal_agg"] if resp["temporal_agg"] else "",
                        placetype=resp["placetype"] if resp["placetype"] else "",
                    ),
                )
                query_results.append(result)
            return QueryResult(query=query.query, results=query_results)

        return await asyncio.gather(*[_single_query(query) for query in queries])

    async def delete(
        self,
        class_name: str,
        ids: Optional[List[str]] = None,
        filter: Optional[DocumentMetadataFilter] = None,
        delete_all: Optional[bool] = None,
    ) -> bool:
        # TODO
        """
        Removes vectors by ids, filter, or everything in the datastore.
        Returns whether the operation was successful.
        """
        if delete_all:
            logger.debug(f"Deleting all vectors in index {class_name}")
            self.client.schema.delete_all()
            return True

        if ids:
            operands = [
                {"path": ["document_id"], "operator": "Equal", "valueString": id}
                for id in ids
            ]

            where_clause = {"operator": "Or", "operands": operands}

            logger.debug(f"Deleting vectors from index {class_name} with ids {ids}")
            result = self.client.batch.delete_objects(
                class_name=class_name, where=where_clause, output="verbose"
            )

            if not bool(result["results"]["successful"]):
                logger.debug(
                    f"Failed to delete the following objects: {result['results']['objects']}"
                )

        if filter:
            where_clause = self.build_filters(filter)

            logger.debug(
                f"Deleting vectors from index {class_name} with filter {where_clause}"
            )
            result = self.client.batch.delete_objects(
                class_name=class_name, where=where_clause
            )

            if not bool(result["results"]["successful"]):
                logger.debug(
                    f"Failed to delete the following objects: {result['results']['objects']}"
                )

        return True

    @staticmethod
    def build_filters(filter):
        if filter.source:
            filter.source = filter.source.value

        operands = []
        filter_conditions = {
            "source": {
                "operator": "Equal",
                "value": "query.filter.source.value",
                "value_key": "valueString",
            },
            "start_date": {"operator": "GreaterThanEqual", "value_key": "valueDate"},
            "end_date": {"operator": "LessThanEqual", "value_key": "valueDate"},
            "default": {"operator": "Equal", "value_key": "valueString"},
        }

        for attr, value in filter.__dict__.items():
            if value is not None:
                filter_condition = filter_conditions.get(
                    attr, filter_conditions["default"]
                )
                value_key = filter_condition["value_key"]

                operand = {
                    "path": [
                        attr
                        if not (attr == "start_date" or attr == "end_date")
                        else "created_at"
                    ],
                    "operator": filter_condition["operator"],
                    value_key: value,
                }

                operands.append(operand)

        return {"operator": "And", "operands": operands}

    @staticmethod
    def _is_valid_weaviate_id(candidate_id: str) -> bool:
        """
        Check if candidate_id is a valid UUID for weaviate's use

        Weaviate supports UUIDs of version 3, 4 and 5. This function checks if the candidate_id is a valid UUID of one of these versions.
        See https://weaviate.io/developers/weaviate/more-resources/faq#q-are-there-restrictions-on-uuid-formatting-do-i-have-to-adhere-to-any-standards
        for more information.
        """
        acceptable_version = [3, 4, 5]

        try:
            result = uuid.UUID(candidate_id)
            if result.version not in acceptable_version:
                return False
            else:
                return True
        except ValueError:
            return False
