import json
import uvicorn
from fastapi import FastAPI
from database_manager import DatabaseManager
from database_manager.models.agent import Agent
from database_manager.models.response import Response

# Create fast api app
app = FastAPI()

db_manager = DatabaseManager()


@app.post("/", response_model=Response)
def insert_data(agent: Agent):
    db_manager.insert_data(agent.name, agent.description, agent.topics, agent.output_format, agent.is_active)
    return Response(message="Data inserted successfully", status_code=201)


@app.get("/{intent}")
def get_agents(intent: str):
    results = db_manager.similarity_search(intent)

    agents = []
    for result in results:
        for entity in result:
            agents.append({
                "name": entity.get("name"),
                "description": entity.get("description"),
                "output_format": entity.get("output_format"),
            })

    return Response(message=json.dumps(agents), status_code=200)


@app.get("/health/test")
def test():
    return Response(message="Test", status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
