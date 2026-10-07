"""Apply plain data onto a ruamel.yaml round-trip document in place.

``save_project`` serializes a pydantic model, which carries no comments,
blank lines, or quoting. Rewriting the file from that data would erase
everything the user wrote around the values (gh-177), so instead the new
data is merged onto the document loaded from disk: only values that
actually changed are touched, and ruamel keeps the rest as authored.

ruamel attaches the blank lines and comments that sit between two nodes
to the last scalar of the first one, so a map's "tail" (for example the
comment above the next top-level section) lives on its deepest last
entry. The helpers below move that tail along when the last entry is
removed, replaced, or followed by a new key.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import CommentMark
from ruamel.yaml.scalarstring import ScalarString
from ruamel.yaml.tokens import CommentToken

_DASH_LINE = re.compile(r"^( *)-( +)\S")


def roundtrip_yaml(text: str | None = None) -> YAML:
    """Return the ruamel.yaml instance used for every tycoon.yml round trip.

    Lines are never wrapped, and when ``text`` is given its mapping and
    sequence indentation is reused, so saving an unchanged file writes
    back the same bytes.
    """
    ryaml = YAML()
    ryaml.preserve_quotes = True
    ryaml.width = 4096
    ryaml.indent(**_detect_indent(text or ""))
    return ryaml


def _detect_indent(text: str) -> dict[str, int]:
    """Guess ruamel's ``indent()`` settings from the first nested block of each kind."""
    mapping = offset = sequence = None
    parent: int | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        dash = _DASH_LINE.match(line)
        if parent is not None and indent >= parent:
            if dash and offset is None:
                offset = indent - parent
                sequence = offset + 1 + len(dash.group(2))
            elif not dash and indent > parent and mapping is None:
                mapping = indent - parent
        parent = indent if line.rstrip().endswith(":") and not dash else None
        if mapping is not None and offset is not None:
            break
    return {"mapping": mapping or 2, "sequence": sequence or 2, "offset": offset or 0}


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
    return _commented(new), True


def _merge_map(doc: CommentedMap, new: dict[str, Any], same_scalar: Callable[[Any, Any], bool]) -> bool:
    changed = False
    tail = _take_tail(doc)
    for key in [k for k in doc if k not in new]:
        # The comments after a removed key introduce the key below it, so
        # they replace the ones the previous key held for the removed one.
        keys = list(doc)
        removed_tail = _take_tail(doc, key)
        idx = keys.index(key)
        if idx > 0:
            _set_tail(doc, removed_tail, keys[idx - 1])
        del doc[key]
        changed = True
    for key, value in new.items():
        if key in doc:
            # Hold the entry's tail aside so it survives a replaced or emptied value.
            entry_tail = _take_tail(doc, key)
            merged, key_changed = merge_into(doc[key], value, same_scalar)
            if merged is not doc[key]:
                doc[key] = merged
            _set_tail(doc, entry_tail, key)
            changed = changed or key_changed
        else:
            doc[key] = _commented(value)
            changed = True
    _mark_empty_as_flow(doc)
    _set_tail(doc, tail)
    return changed


def _merge_seq(doc: CommentedSeq, new: list[Any], same_scalar: Callable[[Any, Any], bool]) -> bool:
    changed = len(doc) != len(new)
    tail = _take_tail(doc)
    del doc[len(new) :]
    for i, value in enumerate(new):
        if i < len(doc):
            item_tail = _take_tail(doc, i)
            merged, item_changed = merge_into(doc[i], value, same_scalar)
            if merged is not doc[i]:
                doc[i] = merged
            _set_tail(doc, item_tail, i)
            changed = changed or item_changed
        else:
            doc.append(_commented(value))
    _mark_empty_as_flow(doc)
    _set_tail(doc, tail)
    return changed


def _mark_empty_as_flow(doc: CommentedMap | CommentedSeq) -> None:
    # An emptied block collection is written as `{}` or `[]`; flagging it as
    # flow style makes ruamel put its tail comment after that, not before it.
    if not len(doc):
        doc.fa.set_flow_style()


def _commented(value: Any) -> Any:
    """Convert plain containers so a tail comment can be attached inside them."""
    if isinstance(value, dict) and not isinstance(value, CommentedMap):
        return CommentedMap((k, _commented(v)) for k, v in value.items())
    if isinstance(value, list) and not isinstance(value, CommentedSeq):
        return CommentedSeq(_commented(v) for v in value)
    return value


def _tail_slot(node: Any, key: Any = None) -> tuple[Any, Any, int] | None:
    """Find ``(container, key, position)`` of the comment slot after ``node``'s last value.

    With ``key``, start from that entry of ``node`` instead of its last one.
    Block collections are descended into; a scalar or a flow collection
    such as ``{}`` holds the slot itself.
    """
    while isinstance(node, (CommentedMap, CommentedSeq)) and len(node):
        if key is None:
            key = next(reversed(node)) if isinstance(node, CommentedMap) else len(node) - 1
        child = node[key]
        if isinstance(child, (CommentedMap, CommentedSeq)) and len(child) and not child.fa.flow_style():
            node, key = child, None
            continue
        return node, key, 2 if isinstance(node, CommentedMap) else 0
    return None


def _take_tail(node: Any, key: Any = None) -> str | None:
    """Detach the lines after the last scalar's own line, keeping its inline comment."""
    slot = _tail_slot(node, key)
    if slot is None:
        return None
    container, k, pos = slot
    entry = container.ca.items.get(k)
    token = entry[pos] if entry else None
    if token is None:
        return None
    value = token.value
    first_line, _, rest = value.partition("\n")
    if first_line.strip().startswith("#"):
        entry[pos] = CommentToken(first_line + "\n", token.start_mark, None)
    else:
        entry[pos] = None
    return rest or None


def _set_tail(node: Any, tail: str | None, key: Any = None) -> None:
    """Replace the lines after the last scalar's own line with ``tail``."""
    slot = _tail_slot(node, key)
    if slot is None:
        return
    container, k, pos = slot
    entry = container.ca.items.get(k)
    token = entry[pos] if entry else None
    inline = None
    if token is not None and token.value.strip().startswith("#"):
        inline = token.value.partition("\n")[0] + "\n"
    if inline is None and not tail:
        if entry:
            entry[pos] = None
        return
    value = (inline or "\n") + (tail or "")
    mark = token.start_mark if token is not None else CommentMark(0)
    if entry is None:
        entry = container.ca.items[k] = [None, None, None, None]
    entry[pos] = CommentToken(value, mark, None)
