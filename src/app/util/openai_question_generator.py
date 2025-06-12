import os

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def generate_question(field: str, difficulty: str) -> dict:
    """
    Use OpenAI to generate a question in the given field and difficulty.
    """
    prompt = f"""
    Generate a multiple choice IQ question in the field of {field} with {difficulty} difficulty.
    Respond in this JSON format:
    {{
      "question": "...",
      "choices": ["...", "...", "...", "..."],
      "answer": "...",
      "explanation": "..."
    }}
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or gpt-3.5-turbo
            messages=[
                {"role": "system", "content": "You are an expert quiz question generator."},
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        # Extract and parse response
        content = response["choices"][0]["message"]["content"]
        import json

        question = json.loads(content)
        question["id"] = f"{field}-{difficulty}-ai"
        question["difficulty"] = difficulty
        question["field"] = field
        return question

    except Exception as e:
        raise RuntimeError(f"OpenAI question generation failed: {e!s}") from e
