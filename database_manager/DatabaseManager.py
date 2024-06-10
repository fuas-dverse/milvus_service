import os
from dotenv import load_dotenv
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from sentence_transformers import SentenceTransformer

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64

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
            FieldSchema(name="topics", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_capacity=100, max_length=100),
            FieldSchema(name="output_format", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="is_active", dtype=DataType.BOOL),
            FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=384)
        ]
        schema = CollectionSchema(fields, "Database collection where context of agents will be stored.")
        return Collection(self.collection_name, schema)

    def insert_data(self, name, description, topics, output_format, is_active=True):

        # Load public key and encrypt name and description
        public_key =  os.environ.get("PUBLIC_KEY") # replace with your public key path
        encrypted_name = self.encrypt_with_public_key(public_key, name.encode())
        encrypted_description = self.encrypt_with_public_key(public_key, description.encode())

        # Convert encrypted bytes to Base64 strings
        base64_name = base64.b64encode(encrypted_name).decode()
        base64_description = base64.b64encode(encrypted_description).decode()

        embeddings = self.generate_embeddings(topics)

        entities = [
            [base64_name],
            [base64_description],
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
        return self.decrypt_results(results)

    ### Encryption and Decryption methods
    # In the following method you can encrypt a variable/string to be encrypted by the public key 
    def encrypt_with_public_key(self, public_key_str, message):
        
        public_key = serialization.load_pem_public_key(
            public_key_str.encode(),
            backend=default_backend()
        )

        encrypted = public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return encrypted
    
    # As the env file is not good to save the private key I keep it in the orginal file and load this
    def read_private_key(self):
        try:
            with open("./KeyGeneration/private_key.pem", "r") as file:
                private_key = file.read()
            return private_key
        except FileNotFoundError:
            print("The specified file does not exist.")

    def decrypt_with_private_key(self, ciphertext):

        private_key_str = self.read_private_key()#os.environ.get("PRIVATE_KEY")

        # Check if the private key string is None or empty
        if not private_key_str:
            raise ValueError("The PRIVATE_KEY environment variable is not set or is empty.")
        
        try:
            private_key = serialization.load_pem_private_key(
                private_key_str.encode(),
                password=None,
                backend=default_backend()
            )
        except ValueError as e:
            print("Error")
            raise ValueError("Could not load the private key. The key may be encrypted, in which case you need to provide the password.") from e

        print("loaded key")

        decrypted = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return decrypted.decode()


    # In thsi function you give the result of the collection search and it will give you the decrypted results back
    def decrypt_results(self, results):
        decrypted_results = []
        for hits in results:
            for hit in hits:
                # Convert Base64 strings back to bytes
                encrypted_name = base64.b64decode(hit.entity.get("name"))
                encrypted_description = base64.b64decode(hit.entity.get("description"))

                # get decrypted values
                decrypted_name = self.decrypt_with_private_key(encrypted_name)
                decrypted_description = self.decrypt_with_private_key(encrypted_description)
                
                # Create a new dictionary with the decrypted name and description
                decrypted_entity = {
                    "name": decrypted_name,
                    "description": decrypted_description,
                    "topics": hit.entity.get("topics"),
                    "output_format": hit.entity.get("output_format"),
                    "is_active": hit.entity.get("is_active"),
                    "embeddings": hit.entity.get("embeddings"),
                }

                # Create a new hit with the decrypted entity                
                hit_dict = {
                    "id": hit.id,
                    "distance": hit.distance,
                    "score": hit.score,
                    "entity":decrypted_entity
                    }
            
                decrypted_results.append(hit_dict)

        return decrypted_results

