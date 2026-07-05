"""Graph JSON for the visualizer — nodes = concepts, edges = resolved cross-links."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_concept_repo, get_edge_repo
from app.models import GraphEdge, GraphNode, GraphResponse
from app.repository import SqlConceptRepository, SqlEdgeRepository

router = APIRouter(tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
def graph(
    concepts: SqlConceptRepository = Depends(get_concept_repo),
    edges: SqlEdgeRepository = Depends(get_edge_repo),
) -> GraphResponse:
    nodes = concepts.all()
    node_ids = {n.id for n in nodes}
    return GraphResponse(
        nodes=[GraphNode(id=n.id, type=n.type, title=n.title) for n in nodes],
        edges=[
            GraphEdge(source=e.source_id, target=e.target_id, resolved=e.resolved)
            for e in edges.all()
            if e.target_id in node_ids  # drop dangling edges (no node to attach)
        ],
    )
