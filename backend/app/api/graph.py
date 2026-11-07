from typing import Annotated
from fastapi import APIRouter, Depends, Request
from ..application.graph import GraphService
from ..domain.catalog import GraphResponse

router = APIRouter(prefix="/api/v2", tags=["graph"])


def graph_service(request: Request) -> GraphService:
    return request.app.state.services.graph


@router.get("/graph", response_model=GraphResponse)
def graph(service: Annotated[GraphService, Depends(graph_service)]) -> GraphResponse:
    return service.graph()
