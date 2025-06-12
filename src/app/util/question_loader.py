import json
import random
from pathlib import Path

# Path to the folder containing your question files
QUESTIONS_DIR = Path(__file__).parent.parent / "questions"

# In-memory cache of loaded questions
question_bank: dict[str, list[dict]] = {}


def load_questions_for_field(field: str) -> list[dict]:
    """
    Loads and caches questions for a given field from its JSON file.
    """
    if field in question_bank:
        return question_bank[field]

    file_path = QUESTIONS_DIR / f"{field}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Questions file not found for field: {field}")

    with open(file_path, encoding="utf-8") as f:
        questions = json.load(f)

    question_bank[field] = questions
    return questions


def get_question(field: str, difficulty: str, exclude_ids: list[str] | None = None) -> dict:
    """
    Returns a random unused question for the field and difficulty.
    """
    exclude_ids = exclude_ids or []

    questions = load_questions_for_field(field)
    filtered = [q for q in questions if q["difficulty"] == difficulty and q["id"] not in exclude_ids]

    if not filtered:
        raise ValueError(f"No more {difficulty} questions left for field '{field}'.")

    return random.choice(filtered)
