import json
import os
from dotenv import load_dotenv
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from sentence_transformers import SentenceTransformer

load_dotenv()


class DatabaseManager:
    def __init__(self):
        self.collection_name = "agents"
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.init_milvus()

    def init_milvus(self):
        connections.connect("default", uri=os.environ.get("MILVUS_URI"), token=os.environ.get("MILVUS_TOKEN"))

        if not self.check_collection():
            self.create_collection()

    def check_collection(self):
        return utility.has_collection(self.collection_name)

    def create_collection(self):
        fields = [
            FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
            FieldSchema(name="name", dtype=DataType.VARCHAR, max_length=800),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=800),
            FieldSchema(name="topics", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=100,
                        max_length=100),
            FieldSchema(name="output_format", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="is_active", dtype=DataType.BOOL),
            FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]
        schema = CollectionSchema(fields, "Database collection where context of agents will be stored.")
        return Collection(self.collection_name, schema)

    def insert_data(self, name, description, topics, output_format, is_active=True):
        embeddings = self.generate_embeddings(topics)

        entities = [
            [name],
            [description],
            [topics],
            [output_format],
            [is_active],
            [embeddings]
        ]

        collection = Collection(self.collection_name)
        collection.insert(entities)

        collection.flush()
        self.create_index()

    def generate_embeddings(self, topics):
        return self.embedding_model.encode(", ".join(topics))

    def create_index(self):
        index = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 128}
        }
        collection = Collection(self.collection_name)
        collection.create_index(field_name="embeddings", index_params=index)

    def similarity_search(self, topics):
        collection = Collection(self.collection_name)
        collection.load()
        vector_to_search = self.generate_embeddings(topics)
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[vector_to_search],
            anns_field="embeddings",
            param=search_params,
            limit=10,
            output_fields=["name", "description", "output_format"]
        )

        # Decrypt the name and description of each agent
        return results

    def get_topics(self):
        collection = Collection(self.collection_name)
        collection.load()
        result = collection.query(
            expr="pk != ''",
            output_fields=["topics"]
        )

        topics = []
        for result in result:
            for topic in result.get("topics"):
                topics.append(topic)

        return list(set(topics))
