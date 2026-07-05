# EduGenie Learning Assistant

EduGenie is a FastAPI and Jinja2 learning application that provides:

- Educational question answering
- Audience-aware concept explanations
- Three-question interactive quizzes
- Concise text summaries
- Structured learning paths

Gemini powers the cloud features. Explanations can optionally run locally with
`MBZUAI/LaMini-Flan-T5-783M`.

## Requirements

- Python 3.10 or newer
- A Gemini API key for live AI responses
- Python 3.11 or 3.12 recommended if using the optional local LaMini model

## Local setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the application and test dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Create `.env` from the example and add your Gemini API key:

```bash
cp .env.example .env
```

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
EXPLANATION_PROVIDER=gemini
```

The existing `.env` can be kept if it is already configured. Never commit it.

Run the application:

```bash
uvicorn app.main:app --reload
```

Open:

- Application: <http://127.0.0.1:8000>
- API documentation: <http://127.0.0.1:8000/docs>
- Health endpoint: <http://127.0.0.1:8000/api/v1/health>

## Optional local explanations

The local model is intentionally optional because PyTorch and the model weights
are much larger than the core application.

```bash
python -m pip install -r requirements-lamini.txt
```

Then set:

```dotenv
EXPLANATION_PROVIDER=lamini
```

The first explanation request downloads the model from Hugging Face and may
take several minutes. The model is loaded only once and subsequent inference
runs locally. Use `EXPLANATION_PROVIDER=gemini` to avoid the download.

## Testing

The test suite mocks all AI calls, so it is deterministic and does not consume
API quota:

```bash
pytest
```

With the server running and a working key, exercise every live provider route:

```bash
python scripts/live_smoke.py
```

## API contracts

| Endpoint | Request |
| --- | --- |
| `POST /api/v1/qa` | `{"question": "..."}` (returns a direct answer and concise rationale) |
| `POST /api/v1/explanations` | `{"topic": "...", "audience_level": "beginner"}` |
| `POST /api/v1/quizzes` | `{"text": "...", "question_count": 10}` (1–10 questions) |
| `POST /api/v1/summaries` | `{"text": "..."}` |
| `POST /api/v1/learning-paths` | `{"topic": "...", "level": "beginner"}` (`beginner`, `intermediate`, `advanced`, or `all`) |

Inputs are length-limited and unknown fields are rejected. Provider errors are
converted into safe API responses; raw credentials and stack traces are never
sent to the browser.

## Production deployment

The production architecture deliberately separates the public frontend from
the secret-bearing API:

- GitHub Pages serves the static interface.
- Google Cloud Run executes the FastAPI backend.
- Google Secret Manager supplies `GEMINI_API_KEY` to Cloud Run.

The Pages workflow reads the backend address from the repository variable
`API_BASE_URL`. It will safely skip deployment until that variable exists.

Cloud Run should be configured with:

```dotenv
GEMINI_MODEL=gemini-2.5-flash
EXPLANATION_PROVIDER=gemini
ALLOWED_ORIGINS=https://ap24110011956.github.io
```

Build the Pages artifact locally after the backend is deployed:

```bash
API_BASE_URL=https://your-cloud-run-service.run.app python scripts/build_pages.py
```

Never add the real Gemini key to the repository, a Pages variable, or frontend
JavaScript. Store it only as a Cloud Run secret.
