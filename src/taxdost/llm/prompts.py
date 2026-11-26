"""Load and list versioned prompt files."""

import re
from pathlib import Path

from taxdost.config import get_settings

PROMPT_PATTERN = re.compile(r"^(?P<task>[a-z][a-z0-9_]*)_v(?P<version>\d+)\.md$")


def find_prompt_versions(task: str, directory: Path | None = None) -> list[Path]:
    """Find a task's prompt files and return them in version order."""
    if not re.fullmatch(r"[a-z][a-z0-9_]*", task):
        raise ValueError(f"Invalid prompt task name: {task}")

    prompt_dir = directory or get_settings().prompts_dir
    prompts = []

    for path in prompt_dir.glob(f"{task}_v*.md"):
        match = PROMPT_PATTERN.fullmatch(path.name)
        if match and match.group("task") == task:
            prompts.append((int(match.group("version")), path))

    return [path for _, path in sorted(prompts, key=lambda item: item[0])]


def load_prompt(
    task: str,
    version: int | None = None,
    directory: Path | None = None,
) -> str:
    """Load a specific prompt version, or the latest version when omitted."""
    versions = find_prompt_versions(task, directory)

    if not versions:
        raise FileNotFoundError(f"No prompt versions found for task: {task}")

    if version is None:
        selected = versions[-1]
    else:
        selected = next(
            (
                path
                for path in versions
                if int(PROMPT_PATTERN.fullmatch(path.name).group("version")) == version
            ),
            None,
        )
        if selected is None:
            raise FileNotFoundError(f"Prompt {task}_v{version}.md not found")

    return selected.read_text(encoding="utf-8").strip()
