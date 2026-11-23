import json
from pathlib import Path

ANSWERS_PATH = Path(__file__).with_name("answers.json")

with ANSWERS_PATH.open("r", encoding="utf-8") as f:
    ANSWERS = json.load(f)


def answer(key: str, **kwargs) -> str:
    value = ANSWERS

    for part in key.split("."):
        value = value[part]

    return value.format(**kwargs)