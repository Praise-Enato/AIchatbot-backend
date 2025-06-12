from datetime import datetime
from typing import Literal, TypedDict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.dynamodb import answers_table
from app.util.question_loader import get_question, load_questions_for_field

# --- Session structure ---


class UserSession(TypedDict):
    field: str
    asked: list[str]
    score: int
    streak: int
    difficulty: str


user_sessions: dict[str, UserSession] = {}

router = APIRouter()

FIELD_OPTIONS = ["math", "logic", "language", "programming"]

# --- Request Models ---


class QuizStartRequest(BaseModel):
    user_id: str
    field: Literal["math", "logic", "language", "programming"]


# --- Response Models ---


class QuizStartResponse(BaseModel):
    message: str
    field: str


class QuizQuestion(BaseModel):
    question_id: str
    field: str
    question: str
    choices: list[str]
    difficulty: str | None = "easy"


# --- Routes ---


@router.post("/quiz/start", response_model=QuizStartResponse)
async def start_quiz(payload: QuizStartRequest) -> QuizStartResponse:
    field = payload.field.lower()

    if field not in FIELD_OPTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported field: {field}")

    return QuizStartResponse(
        message=f"Great! Let's begin your IQ test in the field of {field}.",
        field=field,
    )


@router.post("/quiz/next", response_model=QuizQuestion)
async def get_next_question(payload: QuizStartRequest) -> QuizQuestion:
    user_id = payload.user_id
    field = payload.field.lower()

    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "field": field,
            "asked": [],
            "score": 0,
            "streak": 0,
            "difficulty": "easy",
        }

    session: UserSession = user_sessions[user_id]

    try:
        question = get_question(
            field=field,
            difficulty=session["difficulty"],
            exclude_ids=session["asked"],
        )
    except ValueError:
        from app.util.openai_question_generator import generate_question

        question = generate_question(field, session["difficulty"])

    session["asked"].append(question["id"])

    return QuizQuestion(
        question_id=question["id"],
        field=question["field"],
        question=question["question"],
        choices=question["choices"],
        difficulty=question["difficulty"],
    )


# --- Answer Submission Route ---


class QuizAnswerRequest(BaseModel):
    user_id: str
    question_id: str
    answer: str


class QuizAnswerResponse(BaseModel):
    correct: bool
    explanation: str


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
async def submit_answer(payload: QuizAnswerRequest) -> QuizAnswerResponse:
    user_id = payload.user_id
    question_id = payload.question_id

    if user_id not in user_sessions:
        raise HTTPException(status_code=400, detail="Session not found. Start the quiz first.")

    session: UserSession = user_sessions[user_id]
    field = session["field"]

    questions = load_questions_for_field(field)
    question = next((q for q in questions if q["id"] == question_id), None)

    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    correct = payload.answer.strip().lower() == question["answer"].strip().lower()

    if correct:
        session["score"] += 1
        session["streak"] += 1
    else:
        session["streak"] = 0

    def adjust_difficulty(current: str, up: bool) -> str:
        order = ["easy", "medium", "hard"]
        i = order.index(current)
        if up and i < 2:
            return order[i + 1]
        if not up and i > 0:
            return order[i - 1]
        return current

    if correct and session["streak"] >= 2:
        session["difficulty"] = adjust_difficulty(session["difficulty"], up=True)
        session["streak"] = 0
    elif not correct:
        session["difficulty"] = adjust_difficulty(session["difficulty"], up=False)

    try:
        answers_table.put_item(
            Item={
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "question_id": question["id"],
                "field": field,
                "difficulty": question["difficulty"],
                "given_answer": payload.answer,
                "correct": correct,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log answer to DynamoDB: {e!s}") from e

    return QuizAnswerResponse(correct=correct, explanation=question["explanation"])
