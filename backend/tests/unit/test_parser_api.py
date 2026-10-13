from app.api.parser import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_parser_status_placeholder():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/parser/status")

    assert response.status_code == 200
    assert response.json() == {"status": "placeholder"}
