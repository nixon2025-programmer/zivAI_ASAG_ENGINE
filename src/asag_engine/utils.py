import orjson
from typing import Any

def to_json(obj: Any) -> str:
    return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode("utf-8")
