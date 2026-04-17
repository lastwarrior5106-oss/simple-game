import json
import re
from datetime import time
from typing import Any


def json_serializer(obj: Any, **kwargs) -> str:
    obj = datetime_serializer(obj)
    return json.dumps(obj, default=str, **kwargs)


def datetime_serializer(obj: Any) -> Any:
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj[key] = datetime_serializer(value)
        return obj

    if isinstance(obj, list):
        return [datetime_serializer(item) for item in obj]

    if hasattr(obj, "isoformat"):
        return obj.isoformat()

    if isinstance(obj, time):
        return obj.strftime("%H:%M:%S")

    return obj


def camel_to_title_case(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", text).title()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def email_validator(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def format_validation_error(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted_errors = []

    for error in errors:
        err = error.copy()
        loc = err.get("loc", [])
        msg = err.get("msg", "")

        if "value is not a valid integer" in msg or "value is not a valid float" in msg:
            constraint = "Invalid data type"
        elif "ensure this value is greater than or equal to" in msg:
            constraint = "Minimum value constraint violated (ge)"
        elif "ensure this value is less than or equal to" in msg:
            constraint = "Maximum value constraint violated (le)"
        elif "ensure this value is greater than" in msg:
            constraint = "Value must be greater than specified constraint (gt)"
        elif "ensure this value is less than" in msg:
            constraint = "Value must be less than specified constraint (lt)"
        else:
            constraint = msg

        formatted_errors.append({
            "location": loc,
            "constraint": constraint,
        })

    return formatted_errors