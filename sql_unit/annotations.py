from typing import Any

import yaml


def get_comments(template_str: str) -> str:
    """Extract all block comments from a Jinja2 SQL template string, primarily those which contain "# sql-unit" and
    return them as a single string with normalized indentation and trailing whitespace removed."""
    comment_doc = ""
    while template_str.find("/*") != -1:
        start = template_str.find("/*") + 2
        end = template_str.find("*/", start)
        if end == -1:
            break
        comment = template_str[start:end]
        template_str = template_str[end + 2 :]
        if "# sql-unit" in comment and "# sql-unit.disabled" not in comment:
            comment_doc += comment.replace("# sql-unit", "") + "\n"
    comment_doc = comment_doc
    if not comment_doc:
        return ""
    # Normalize indentation
    lines = comment_doc.splitlines()
    nonempty_lines = [line for line in lines if line.strip()]
    if not nonempty_lines:
        return ""
    min_indent = min((len(line) - len(line.lstrip())) for line in nonempty_lines)
    normalized = "\n".join(line[min_indent:] for line in nonempty_lines)
    # Remove trailing whitespace
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines())
    return normalized


def get_comments_obj(template_str: str) -> dict[str, Any]:
    """Extract comments from a Jinja2 SQL template string and return them as a dictionary."""
    comments = get_comments(template_str)
    if not comments:
        return {}
    try:
        result = yaml.safe_load(comments)
        return result
    except yaml.YAMLError:
        return {}
        # raise ValueError(f"Failed to parse comments as YAML: {e}") from e


def get_template_variables(template_str: str) -> set[str]:
    """Extract variable names from a Jinja2 template string."""
    from jinja2 import Environment, meta

    env = Environment()
    ast = env.parse(template_str)
    return set(meta.find_undeclared_variables(ast))
