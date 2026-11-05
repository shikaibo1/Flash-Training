"""Compatibility entry point: python -m uvicorn api_server:app --port 8001."""
from app.main import create_app

app = create_app()
