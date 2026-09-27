"""Apply plain data onto a ruamel.yaml round-trip document in place.

``save_project`` serializes a pydantic model, which carries no comments,
blank lines, or quoting. Rewriting the file from that data would erase
everything the user wrote around the values (gh-177), so instead the new
data is merged onto the document loaded from disk: only values that
actually changed are touched, and ruamel keeps the rest as authored.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import ScalarString


def roundtrip_yaml() -> YAML:
    """Return the ruamel.yaml instance used for every tycoon.yml round trip."""
    ryaml = YAML()
    ryaml.preserve_quotes = True
    return ryaml


def merge_into(doc: Any, new: Any, same_scalar: Callable[[Any, Any], bool]) -> tuple[Any, bool]:
    """Merge ``new`` onto ``doc`` and return ``(result, changed)``.

    Mappings are updated key by key, sequences index by index, and a scalar
    is replaced only when ``same_scalar(old, new)`` is false, so an untouched
    value keeps its original quoting and any comment attached to it.
    """
    if isinstance(doc, CommentedMap) and isinstance(new, dict):
        return doc, _merge_map(doc, new, same_scalar)
    if isinstance(doc, CommentedSeq) and isinstance(new, list):
        return doc, _merge_seq(doc, new, same_scalar)
    if not isinstance(doc, (dict, list)) and not isinstance(new, (dict, list)) and same_scalar(doc, new):
        return doc, False
    if isinstance(doc, ScalarString) and isinstance(new, str):
        # Keep a literal or folded block style when a multi-line value changes.
        return type(doc)(new), True
    return new, True


def _merge_map(doc: CommentedMap, new: dict[str, Any], same_scalar: Callable[[Any, Any], bool]) -> bool:
    changed = False
    for key in [k for k in doc if k not in new]:
        del doc[key]
        changed = True
    for key, value in new.items():
        if key in doc:
            merged, key_changed = merge_into(doc[key], value, same_scalar)
            if merged is not doc[key]:
                doc[key] = merged
            changed = changed or key_changed
        else:
            doc[key] = value
            changed = True
    return changed


def _merge_seq(doc: CommentedSeq, new: list[Any], same_scalar: Callable[[Any, Any], bool]) -> bool:
    changed = len(doc) != len(new)
    del doc[len(new) :]
    for i, value in enumerate(new):
        if i < len(doc):
            merged, item_changed = merge_into(doc[i], value, same_scalar)
            if merged is not doc[i]:
                doc[i] = merged
            changed = changed or item_changed
        else:
            doc.append(value)
    return changed
