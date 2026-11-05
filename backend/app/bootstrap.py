"""The composition root is the only place connecting application and infrastructure."""
from dataclasses import dataclass
from .application.content import ContentService
from .application.skills import SkillService
from .application.practice import PracticeService
from .application.progress import ProgressService
from .application.records import RecordService
from .domain.ports import JSONClient, UnitOfWorkFactory


@dataclass(frozen=True)
class Services:
    skills: SkillService
    practice: PracticeService
    progress: ProgressService
    records: RecordService


def build_services(work: UnitOfWorkFactory, client: JSONClient) -> Services:
    content = ContentService(client)
    return Services(SkillService(work, content), PracticeService(work, content),
                    ProgressService(work, content), RecordService(work))
