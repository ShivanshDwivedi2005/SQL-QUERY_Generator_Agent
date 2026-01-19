# AI-SQL-Agent

AI-SQL-Agent is a project that helps generate, validate, and run SQL queries using AI-assisted tools. This repository contains a mix of TypeScript and Python code to provide an interactive agent, utilities, and integrations for working with SQL databases.

## Languages
- React + Typescript
- Python

## Features
- Use AI to translate natural-language questions into SQL queries
- Validate and explain generated SQL
- Run queries against a connected database safely (with configuration)
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

3. Set up Python environment (optional — for Python utilities)

```bash
python -m venv .venv
source .venv/bin/activate  # on macOS/Linux
.\.venv\Scripts\activate   # on Windows
pip install -r requirements.txt
```

4. Configuration

Create a .env file at the repository root and add the required environment variables. Example:

```
# .env
OPENAI_API_KEY=sk-xxx
```

5. Run the project

The repository contains both TypeScript and Python parts. Typical commands (adjust to your project scripts):

```bash
# Build and run TypeScript app
npm run build
npm start
# or for development
npm run dev
```
