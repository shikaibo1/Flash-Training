from __future__ import annotations
from ..domain.learning import event_time, next_mastery
from ..domain.models import MasteryEvent
from ..domain.ports import UnitOfWork


def record_performance(unit: UnitOfWork, user_id: str, atom_id: str, performance: float,
                       timestamp: str | None = None, session_id: str | None = None,
                       provenance: str = "live") -> float:
    """Participate in the caller's transaction, including practice completion."""
    unit.skills.atom(atom_id)
    stamp = event_time(timestamp, provenance)
    last = unit.progress.latest_mastery(user_id, atom_id)
    value = next_mastery(performance, last.mastery if last else 0.0, stamp, last.timestamp if last else None)
    unit.users.ensure(user_id)
    unit.progress.add_event(user_id, atom_id, MasteryEvent(timestamp=stamp, performance=performance, mastery=value),
                            session_id, provenance)
    return value
