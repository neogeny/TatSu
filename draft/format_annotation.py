from typing import get_args, get_origin


def format_annotation(tp) -> str:
    origin = get_origin(tp)
    args = get_args(tp)

    if not origin:
        # It's a base type like int or str, just grab its name
        return getattr(tp, "__name__", str(tp))

    # Handle modern Unions (str | int) vs Legacy Unions (typing.Union)
    if origin is getattr(types, "UnionType", None) or str(origin) == "typing.Union":
        return " | ".join(format_annotation(arg) for arg in args)

    # Handle standard generics like list[...] or dict[...]
    origin_name = getattr(origin, "__name__", str(origin))
    arg_strings = ", ".join(format_annotation(arg) for arg in args)
    return f"{origin_name}[{arg_strings}]"


# Test it out on a deeply nested messy type object
complex_dynamic_type = list[dict[str, int | float]]
print(format_annotation(complex_dynamic_type))
# Output: list[dict[str, int | float]]
