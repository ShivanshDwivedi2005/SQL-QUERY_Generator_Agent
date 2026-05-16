# AI-SQL-Agent

AI-SQL-Agent is a project that helps generate, validate, and run PostgreSQL queries using AI-assisted tools. This repository contains a React frontend and Python/FastAPI backend for asking questions against a Neon PostgreSQL database.

## Languages
- React + Typescript
- Python

## Features
- Use AI to translate natural-language questions into SQL queries
- Validate and explain generated SQL
- Run read-only queries against a connected Neon PostgreSQL database
- Modular codebase with TypeScript frontend/agent logic and Python utilities/scripts

---

## Screenshots

<img width="1850" height="932" alt="image" src="https://github.com/user-attachments/assets/c6c4706a-531b-4310-90eb-c21e79470a62" />

<img width="1850" height="932" alt="image" src="https://github.com/user-attachments/assets/47b0be63-af51-409a-a2a9-e77fa2c516d4" />

---

1. Clone the repository

```bash
git clone https://github.com/OmAmar106/AI-SQL-Agent.git
cd AI-SQL-Agent
```

2. Install Node dependencies

```bash
# using npm
npm install
# or using pnpm
pnpm install
```

3. Set up Python environment

```bash
python -m venv .venv
source .venv/bin/activate  # on macOS/Linux
.\.venv\Scripts\activate   # on Windows
cd backend
pip install -r requirements.txt
```

4. Configuration

Create a `.env` file in `backend/` and add the required environment variables. Example:

```
# .env
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

You can also use `NEON_DATABASE_URL` instead of `DATABASE_URL`.

Create a `.env` file in `frontend/`:

```
VITE_API_URL=http://localhost:8000
```

5. Run the project

The repository contains both TypeScript and Python parts. Typical commands (adjust to your project scripts):

```bash
# backend
cd backend
uvicorn apis:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev
```
