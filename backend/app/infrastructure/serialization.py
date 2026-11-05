from __future__ import annotations
import json
from pydantic import BaseModel
from ..domain.models import JsonValue


def dump(value: BaseModel | JsonValue) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(value, ensure_ascii=False, allow_nan=False)
