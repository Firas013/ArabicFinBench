"""Helpers that flatten JSON Schema combinators for extract scoring."""

from __future__ import annotations

from extract_bench.inference.providers.extract.table_codegen.schema_utils import (
    resolve_refs,
    schema_items,
    schema_properties,
)


def test_schema_properties_and_items_flatten_inlined_anyof_ref() -> None:
    schema = {
        "type": "object",
        "$defs": {
            "Vendor": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "city": {"type": "string"},
                },
            },
            "Line": {
                "type": "object",
                "properties": {"sku": {"type": "string"}},
            },
        },
        "properties": {
            "vendor": {"anyOf": [{"$ref": "#/$defs/Vendor"}, {"type": "null"}]},
            "lines": {
                "anyOf": [
                    {"type": "array", "items": {"$ref": "#/$defs/Line"}},
                    {"type": "null"},
                ]
            },
        },
    }
    resolved = resolve_refs(schema)
    assert set(schema_properties(resolved["properties"]["vendor"])) == {"name", "city"}
    items = schema_items(resolved["properties"]["lines"])
    assert set(schema_properties(items)) == {"sku"}
