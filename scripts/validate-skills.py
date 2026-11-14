"""Validate the library's Agent Skills metadata and standalone package basics."""
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parent.parent


def validate():
    errors = []
    entries = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not entries:
        errors.append("No skills found under skills/")
    for entry in entries:
        label = str(entry.relative_to(ROOT))
        try:
            text = entry.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                raise ValueError("must begin with YAML frontmatter")
            header, body = text[4:].split("\n---\n", 1)
            data = yaml.safe_load(header)
            if not isinstance(data, dict):
                raise ValueError("frontmatter must be a mapping")
            name = data.get("name", "")
            if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
                raise ValueError("invalid name")
            if name != entry.parent.name:
                raise ValueError("name must match directory")
            description = data.get("description")
            if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
                raise ValueError("description must be a nonempty string of at most 1024 characters")
            if "compatibility" in data:
                value = data["compatibility"]
                if not isinstance(value, str) or not 1 <= len(value.strip()) <= 500:
                    raise ValueError("compatibility must be a nonempty string of at most 500 characters")
            if "metadata" in data:
                value = data["metadata"]
                if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
                    raise ValueError("metadata must map strings to strings")
            if not body.strip():
                raise ValueError("missing skill instructions")
            for filename in ("README.md", "LICENSE"):
                if not (entry.parent / filename).is_file():
                    raise ValueError(f"missing standalone {filename}")
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f"{label}: {exc}")
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(entries)} skill packages.")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
