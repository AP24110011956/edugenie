from fastapi.testclient import TestClient


def test_home_page(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "EduGenie" in response.text
    assert "What would you like to do?" in response.text


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "gemini_configured" in response.json()


def test_cors_allows_configured_local_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/qa",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"


def test_question_answering(client: TestClient) -> None:
    response = client.post("/api/v1/qa", json={"question": "Why is the sky blue?"})
    assert response.status_code == 200
    assert response.json()["model"] == "test-model"
    assert "sky blue" in response.json()["answer"]
    assert response.json()["reasoning"]


def test_explanation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/explanations",
        json={"topic": "photosynthesis", "audience_level": "beginner"},
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "gemini"


def test_quiz_has_requested_structure(client: TestClient) -> None:
    response = client.post(
        "/api/v1/quizzes",
        json={
            "text": "Plants use sunlight, water, and carbon dioxide to make energy.",
            "question_count": 3,
        },
    )
    assert response.status_code == 200
    questions = response.json()["questions"]
    assert len(questions) == 3
    assert all(len(question["options"]) == 4 for question in questions)
    assert all(question["answer"] in question["options"] for question in questions)


def test_quiz_supports_ten_questions(client: TestClient) -> None:
    response = client.post(
        "/api/v1/quizzes",
        json={
            "text": "Plants use sunlight, water, and carbon dioxide to make energy.",
            "question_count": 10,
        },
    )
    assert response.status_code == 200
    assert len(response.json()["questions"]) == 10


def test_summary(client: TestClient) -> None:
    response = client.post(
        "/api/v1/summaries",
        json={"text": "This is a sufficiently long paragraph for a summary request."},
    )
    assert response.status_code == 200
    assert response.json()["summary"] == "A concise test summary."


def test_learning_path(client: TestClient) -> None:
    response = client.post(
        "/api/v1/learning-paths",
        json={"topic": "Python", "level": "beginner"},
    )
    assert response.status_code == 200
    assert response.json()["topic"] == "Python"
    assert response.json()["stages"][0]["title"] == "Foundations"


def test_learning_path_accepts_all_levels(client: TestClient) -> None:
    response = client.post(
        "/api/v1/learning-paths",
        json={"topic": "Python", "level": "all"},
    )
    assert response.status_code == 200
    assert response.json()["level"] == "all"


def test_validation_error_is_safe_and_structured(client: TestClient) -> None:
    response = client.post("/api/v1/qa", json={"question": "x"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "question"
