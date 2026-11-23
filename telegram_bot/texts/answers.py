import json
import re
from pathlib import Path
from string import Formatter

ANSWERS_PATH = Path(__file__).with_name("answers.json")

with ANSWERS_PATH.open("r", encoding="utf-8") as f:
    ANSWERS = json.load(f)


class MarkdownFormatter(Formatter):
    def format_field(self, value, format_spec: str) -> str:
        formatted = super().format_field(value, format_spec)
        return re.sub(r"([_*`\[\]()~>#+\-=|{}.!\\])", r"\\\1", formatted)


markdown_formatter = MarkdownFormatter()


def answer(key: str, *, plain: bool = False, **kwargs) -> str:
    value = ANSWERS

    for part in key.split("."):
        value = value[part]

    if plain:
        return value.format(**kwargs)
    return markdown_formatter.format(value, **kwargs)
