import os
import uuid
from unittest.mock import MagicMock

import chromadb
import loguru
from flask import Flask
from sympy.utilities import pytest

from config import app_config
from rag.datasource.vdb.chroma.chroma_vector import ChromaVector, ChromaConfig
from rag.entities.document import Document
from services.database import redis_db
from services.database.redis_db import redis_client


def get_example_text() -> str:
    return "test_text"

def get_example_document(doc_id: str) -> Document:
    doc = Document(
        page_content=get_example_text(),
        metadata={
            "doc_id": doc_id,
            "doc_hash": doc_id,
            "document_id": doc_id,
            "dataset_id": doc_id,
        },
    )
    return doc


def gen_collection_name_by_id(dataset_id: str) -> str:
    normalized_dataset_id = dataset_id.replace("-", "_")
    return f'Vector_index_{normalized_dataset_id}_Node'


class AbstractVectorTest:
    def __init__(self):
        self.vector = None
        self.dataset_id = str(uuid.uuid4())
        # self.collection_name = gen_collection_name_by_id(self.dataset_id) + "_test"
        self.collection_name = "Vector_index_40590aa6_6318_4a16_9f7f_341a6cc2e2b2_Node_test"
        loguru.logger.info(f"collection_name:{self.collection_name}")
        self.example_doc_id = str(uuid.uuid4())
        self.example_embedding = [1.001 * i for i in range(128)]

    def create_vector(self,texts,embeddings) -> None:
        self.vector.create(
            texts=texts,
            embeddings=embeddings,
        )

    def search_by_vector(self,query_embed):
        hits_by_vector: list[Document] = self.vector.search_by_vector(query_vector=query_embed)
        return hits_by_vector
        # assert len(hits_by_vector) == 1
        # assert hits_by_vector[0].metadata["doc_id"] == self.example_doc_id

    def search_by_full_text(self):
        hits_by_full_text: list[Document] = self.vector.search_by_full_text(query=get_example_text())
        assert len(hits_by_full_text) == 1
        assert hits_by_full_text[0].metadata["doc_id"] == self.example_doc_id

    def delete_vector(self):
        self.vector.delete()

    def delete_by_ids(self, ids: list[str]):
        self.vector.delete_by_ids(ids=ids)

    def add_texts(self) -> list[str]:
        batch_size = 100
        documents = [get_example_document(doc_id=str(uuid.uuid4())) for _ in range(batch_size)]
        embeddings = [self.example_embedding] * batch_size
        self.vector.add_texts(documents=documents, embeddings=embeddings)
        return [doc.metadata["doc_id"] for doc in documents]

    def text_exists(self):
        assert self.vector.text_exists(self.example_doc_id)

    def get_ids_by_metadata_field(self):
        with pytest.raises(NotImplementedError):
            self.vector.get_ids_by_metadata_field(key="key", value="value")

    def run_all_tests(self):
        self.create_vector()
        self.search_by_vector()
        self.search_by_full_text()
        self.text_exists()
        self.get_ids_by_metadata_field()
        added_doc_ids = self.add_texts()
        self.delete_by_ids(added_doc_ids)
        self.delete_vector()


class ChromaVectorTest(AbstractVectorTest):
    def __init__(self):
        super().__init__()
        self.vector = ChromaVector(
            collection_name=self.collection_name,
            config=ChromaConfig(
                host=os.getenv("CHROMA_HOST"),
                port="8000",
                tenant=chromadb.DEFAULT_TENANT,
                database=chromadb.DEFAULT_DATABASE,
                auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
                auth_credentials="starchat123456",
            ),
        )

    def search_by_full_text(self):
        # chroma dos not support full text searching
        hits_by_full_text = self.vector.search_by_full_text(query=get_example_text())
        assert len(hits_by_full_text) == 0

def init_redis():
    class StarApp(Flask):
        pass

    star_app = StarApp(__name__)
    star_app.config.from_mapping(app_config.model_dump())
    redis_db.init_app(star_app)


def test_chroma_vector(texts,embeddings):
    init_redis()
    ChromaVectorTest().create_vector(texts,embeddings)

def test_chroma_vector_search(query_embed):
    init_redis()
    hits_by_vector = ChromaVectorTest().search_by_vector(query_embed)
    return hits_by_vector