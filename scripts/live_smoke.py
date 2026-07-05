"""Exercise all live AI routes against a running local EduGenie server."""

from __future__ import annotations

import sys

import httpx


BASE_URL = "http://127.0.0.1:8000/api/v1"
CASES = {
    "qa": ("/qa", {"question": "Why is the sky blue?"}),
    "explanation": (
        "/explanations",
        {"topic": "photosynthesis", "audience_level": "beginner"},
    ),
    "quiz": (
        "/quizzes",
        {
            "text": (
                "Photosynthesis lets plants convert light energy into chemical "
                "energy. They use carbon dioxide and water to produce glucose "
                "and release oxygen, primarily inside chloroplasts."
            ),
            "question_count": 10,
        },
    ),
    "summary": (
        "/summaries",
        {
            "text": (
                "The water cycle continuously moves water between Earth's "
                "surface and atmosphere through evaporation, condensation, "
                "precipitation, and collection. Solar energy drives the cycle."
            )
        },
    ),
    "learning_path": (
        "/learning-paths",
        {"topic": "Python programming", "level": "all"},
    ),
}


def main() -> int:
    failures = 0
    with httpx.Client(timeout=90) as client:
        for name, (path, payload) in CASES.items():
            response = client.post(f"{BASE_URL}{path}", json=payload)
            data = response.json()
            if response.is_success:
                if name == "quiz":
                    detail = f"questions={len(data['questions'])}"
                elif name == "learning_path":
                    detail = f"stages={len(data['stages'])}"
                else:
                    key = next(key for key in ("answer", "explanation", "summary") if key in data)
                    detail = f"characters={len(data[key])}"
                print(f"PASS {name}: HTTP {response.status_code}, {detail}")
            else:
                failures += 1
                message = data.get("error", {}).get("message", "Unknown error")
                print(f"FAIL {name}: HTTP {response.status_code}, {message}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
