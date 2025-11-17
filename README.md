# HRI Autism Backend

Built with FastAPI, this service supports authenticated parents/therapists who register/login, manage their own children, and create daily sessions. Each child’s long-term profile plus daily context is processed through OpenAI (keywords + prompts), and the results—together with all relational data—are stored in Google Sheets for downstream use in the social robot workflow. Every API call is protected by JWT, ensuring users only access the children and sessions they own.

## Prerequisites

- Google service account credentials with edit access to the target spreadsheet.
- OpenAI API key with access to `gpt-4o-mini` (keywords) and `gpt-4o` (prompts).
- JWT symmetric secret for signing authentication tokens.

## API Surface

| Method | Path                                         | Description                                                  |
|--------|-----------------------------------------------|--------------------------------------------------------------|
| POST   | `/api/auth/register`                          | Register user and return JWT                                 |
| POST   | `/api/auth/login`                             | Login via email/password, return JWT                         |
| GET    | `/api/auth/me`                                | Fetch current logged-in user profile                         |
| POST   | `/api/children`                               | Create child (generates keywords, links to current user)     |
| GET    | `/api/children`                               | List all children for current user                           |
| GET    | `/api/children/{child_id}`                    | Retrieve child details (must belong to current user)         |
| GET    | `/api/children/{child_id}/sessions/latest`    | Latest session info for a child, or null if none             |
| POST   | `/api/sessions`                               | Create session and prompt for current user's child           |
| GET    | `/api/sessions/{session_id}`                  | Retrieve session by ID                                       |
| GET    | `/healthz`                                    | Health check & environment report                            |
