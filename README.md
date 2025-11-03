# HRI Autism Backend

Built with FastAPI, this service integrates each child’s long-term profile with daily session inputs from parents or therapists, using the OpenAI API to extract normalized keywords and generate a session-specific system prompt for a social companion robot that supports children on the autism spectrum. All structured data and prompts are stored in Google Sheets for downstream use in the robot’s interaction workflow.

## Prerequisites

- Google service account credentials with edit access to the target spreadsheet.
- OpenAI API key with access to `gpt-4o-mini` (keywords) and `gpt-4o` (prompts).

## API Surface

| Method | Path                          | Description                                |
|--------|------------------------------|--------------------------------------------|
| POST   | `/api/children`              | Create a child profile; generates keywords |
| GET    | `/api/children/{child_id}`   | Retrieve a child profile                   |
| POST   | `/api/sessions`              | Generate a session prompt & store session  |
| GET    | `/api/sessions/{session_id}` | Retrieve a session (prompt + context)      |
| GET    | `/healthz`                   | Health check & environment report          |
