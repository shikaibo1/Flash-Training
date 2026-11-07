from ..domain.catalog import GraphEdge, GraphNode, GraphResponse
from ..domain.ports import UnitOfWorkFactory


class GraphService:
    def __init__(self, work: UnitOfWorkFactory):
        self._work = work

    def graph(self) -> GraphResponse:
        with self._work.read() as unit:
            roles = unit.skills.catalog_roles()
            knowledge = unit.skills.catalog_knowledge()
            atoms = unit.skills.atoms()
            tasks = unit.skills.list(enabled_only=True)
        nodes = []
        for kind, records, id_field in (("role", roles, "role_id"), ("knowledge", knowledge, "knowledge_id"),
                                         ("atom", atoms, "atomic_skill_id"), ("task", tasks, "skill_id")):
            for record in records:
                reference_id = getattr(record, id_field)
                label = record.display_name if kind == "task" else record.name
                nodes.append(GraphNode(id=f"{kind}:{reference_id}", type=kind, label=label,
                                       description=record.description, reference_id=reference_id))
        edges = []
        for task in tasks:
            if task.role_id:
                edges.append(GraphEdge(source=f"role:{task.role_id}", target=f"task:{task.skill_id}", relation="contains"))
            edges.extend(GraphEdge(source=f"task:{task.skill_id}", target=f"atom:{atom_id}", relation="requires")
                         for atom_id in task.atomic_skills)
        for atom in atoms:
            edges.extend(GraphEdge(source=f"knowledge:{knowledge_id}", target=f"atom:{atom.atomic_skill_id}", relation="supports")
                         for knowledge_id in atom.knowledge_ids)
            edges.extend(GraphEdge(source=f"atom:{prior_id}", target=f"atom:{atom.atomic_skill_id}", relation="prerequisite")
                         for prior_id in atom.prerequisite_ids)
        return GraphResponse(nodes=nodes, edges=edges, atoms=atoms, tasks=tasks, roles=roles, knowledge=knowledge)
