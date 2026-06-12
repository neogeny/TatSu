# `fromjson` — Reflective JSON Deserializer

Transforms a JSON-compatible nested structure (dicts, lists, primitives) into
a Python object graph.  The counterpart to `asjson` in `tatsu.util.asjson`.

```
JSON tree  ──→  Python object graph
```

## The `__class__` Protocol

Every serialized object includes a `"__class__"` key naming its Python type.
The dispatch is three-way:

| Input shape                                    | Return type           |
|------------------------------------------------|-----------------------|
| `Mapping` without `"__class__"`                | `dict`                |
| `Mapping` with `"__class__"` → known type      | typed `JSONBase` subclass |
| `Mapping` with `"__class__"` → unknown type    | `Object` instance     |
| `list` / `tuple` / `set`                       | `list`                |
| `None` / `bool` / `int` / `float` / `str`      | same value            |

### Data dict path — no `"__class__"`

A bare `Mapping` without `"__class__"` is pure data with no type metadata.
Returned as-is as a plain `dict`.  All values are recursively deserialized.

```python
fromjson({"a": 1, "b": [2, 3]})
# → {"a": 1, "b": [2, 3]}
```

### Typed path — known `"__class__"`

If `"__class__"` names a registered `JSONBase` subclass, the raw contents of
the dict (including `"__class__"`) are passed to that class's
`__from_json__()` classmethod, which constructs a bare instance via
`__new__` and populates its fields.

Fields are only set if they correspond to an actual attribute on the target
class — either a class-level attribute (`hasattr(cls, name)`) or a dataclass
field (`name in cls.__dataclass_fields__`).  The dataclass check is necessary
because Python's `@dataclass` removes fields declared with
`default_factory=` from the class `__dict__`.

```python
fromjson({"__class__": "Call", "name": "expression"})
# → Call(name="expression")

fromjson({"__class__": "Grammar", "name": "CALC", "rules": [...]})
# → Grammar(name="CALC", rules=[Rule(...), ...])
```

### Fallback path — unknown `"__class__"`

If `"__class__"` is present but does not name a registered type, the dict
is treated as an anonymous structured object and returned as an `Object`
instance with attribute-style access to all non-`"__class__"` keys.

```python
fromjson({"__class__": "UnknownType", "x": 1})
# → <Object with .x == 1>
```

This path exists so that modified or unexpected JSON does not raise; it
degrades gracefully to an opaque bag of attributes.

## Registration

All `JSONBase` subclasses register themselves automatically via
`__init_subclass__` into the module-level `__from_json__class__` dict:

```python
__from_json__class__: dict[str, type] = {}

class JSONBase:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        __from_json__class__[cls.__name__] = cls
```

No manual registration is needed.  Any class that inherits from `JSONBase`
(at any depth) is available for `"__class__"` dispatch as soon as its
module is imported.

## The `Object` Class

A minimal anonymous container for the fallback path:

```python
class Object:
    pass
```

Instances are created by `asobj()` inside `dfs`, which calls `setattr` for
each key-value pair.  `Object` is intentionally bare — no methods, no
custom `__repr__`, no behavior.  Consumers should use `is_object()` from
`tatsu.util.typetools` to distinguish `Object` instances from base types.

## `is_object()` — Type Discrimination

Defined in `tatsu.util.typetools`:

```python
def is_object(obj) -> bool:
    return not (
        obj is None
        or isinstance(obj, bool | int | float | str | bytes | bytearray
                       | list | tuple | set | frozenset | dict)
    )
```

Returns `True` for anything that is not a Python base type — `Object`
instances, `JSONBase` subclasses, dataclasses, custom classes — and
`False` for primitives and standard containers.  This is the intended way
to check whether a `fromjson` return value is a "structured object"
without inspecting its concrete type.

## Dataclass Field Resolution

When `__from_json__` populates fields, it builds a `fieldmap` from the
class's `__dataclass_fields__` (if it is a `@dataclass`).  This catches
fields that are invisible to `hasattr()` because Python's `@dataclass`
deletes class-level attributes for fields declared with
`default_factory=`.

| Declaration                         | `hasattr(cls, name)` | `name in fieldmap` | Resolved |
|-------------------------------------|----------------------|--------------------|----------|
| `name: str = ""`                    | `True`               | `True`             | yes      |
| `sequence: list = field(default_factory=list)` | `False`  | `True`             | yes      |
| `ghost: int` (not a field at all)   | `False`              | `False`            | no       |

Keys that match neither path are silently skipped — they cannot be set on
the target class.

## `jsonimport` Wrapper

`tatsu.grammars.jsonimport` is a thin 30-line wrapper around `fromjson`:

```python
def load_grammar(value: Any) -> g.Grammar:
    result = fromjson(value)
    assert isinstance(result, g.Grammar)
    return result
```

It previously contained a 392-line handwritten factory
(`exp_from_json_path`, `rule_from_json_value`, etc.) that manually
dispatched on type names and called constructors.  The reflective
approach in `fromjson` replaced all of that — new expression types are
handled automatically as long as they inherit from `JSONBase`.

## Roundtrip with `asjson`

`fromjson` is the inverse of `asjson`:

```
Python object  ──asjson()──→  JSON-compatible tree
JSON tree      ──fromjson──→  Python object
```

`asjson` serializes the public fields of a `JSONBase` instance (via
`__pub__()`), producing a dict with `"__class__"`.  `fromjson` reads that
dict back, dispatching on `"__class__"` to reconstruct the correct type
and set its fields.

## Limitations

- **Non-dataclass fields**: a `default_factory` field on a custom
  `JSONBase` subclass that is not a `@dataclass` will not be resolved
  unless it also has a class-level attribute.
- **Extra keys**: JSON keys that do not correspond to any attribute on
  the target class are silently dropped in the typed path.
- **No type coercion**: string-valued fields must already be strings in
  the input; no implicit conversion is performed.
