import json
from pathlib import Path
from typing import Any

# Load schemas once at module level
BASE_DIR = Path(__file__).parent.parent.parent.parent / "contract" / "fixtures"
REQUEST_SCHEMA = json.loads((BASE_DIR / "request_schema.json").read_text())
SHIPMENT_SCHEMA = json.loads((BASE_DIR / "shipment_schema.json").read_text())


def _validate(obj: Any, schema: dict) -> tuple[bool, list[str]]:
    errors = []

    # 1. Check required fields
    for field in schema.get("required", []):
        if field not in obj:
            errors.append(f"Missing required field: {field}")

    # 2. Check types and constraints
    for field, rules in schema.get("properties", {}).items():
        if field not in obj:
            continue

        value = obj[field]

        # Type check
        expected_type = rules.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Field {field} must be a string")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"Field {field} must be an integer")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Field {field} must be a boolean")

        # Enum check
        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"Field {field} must be one of {rules['enum']}")

        # Integer bounds
        if "minimum" in rules and value < rules["minimum"]:
            errors.append(f"Field {field} must be >= {rules['minimum']}")
        if "maximum" in rules and value > rules["maximum"]:
            errors.append(f"Field {field} must be <= {rules['maximum']}")

    return (len(errors) == 0, errors)


def validate_request(obj: Any) -> tuple[bool, list[str]]:
    return _validate(obj, REQUEST_SCHEMA)


def validate_shipment(obj: Any) -> tuple[bool, list[str]]:
    return _validate(obj, SHIPMENT_SCHEMA)
