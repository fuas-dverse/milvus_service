import uvicorn
from fastapi import FastAPI
from Milvus.DatabaseManager import DatabaseManager

# Create fast api app
app = FastAPI()

db_manager = DatabaseManager()


@app.post("/")
def insert_data(name: str, description: str, topics: list, output_format: str, is_active: bool = True):
    db_manager.insert_data(name, description, topics, output_format, is_active)
    return {"status": "success"}


@app.get("/{intent}")
def get_agents(intent: str):
    results = db_manager.similarity_search(intent)

    agents = []

    for result in results:
        for obj in result:
            agents.append(obj)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
