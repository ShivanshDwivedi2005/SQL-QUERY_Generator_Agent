# AI-SQL-Agent

Marketwise Hackathon

AI-SQL-Agent is a project that helps generate, validate, and run SQL queries using AI-assisted tools. This repository contains a mix of TypeScript and Python code to provide an interactive agent, utilities, and integrations for working with SQL databases.

## Languages
- TypeScript (~76.5%)
- Python (~21.4%)
- CSS and other (~2.1%)

## Features
- Use AI to translate natural-language questions into SQL queries
- Validate and explain generated SQL
- Run queries against a connected database safely (with configuration)
- Modular codebase with TypeScript frontend/agent logic and Python utilities/scripts

## Quickstart (local)

### Prerequisites
- Node.js (>=16)
- npm or pnpm
- Python 3.8+ and pip
- A supported SQL database (Postgres, MySQL, etc.)
- An OpenAI-compatible API key or other LLM endpoint if the project uses one

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
DATABASE_URL=postgres://user:pass@localhost:5432/mydb
NODE_ENV=development
```

Adjust variable names to match the project's configuration files if they differ.

5. Run the project

The repository contains both TypeScript and Python parts. Typical commands (adjust to your project scripts):

```bash
# Build and run TypeScript app
npm run build
npm start
# or for development
npm run dev

# Run Python scripts / utilities
python scripts/example.py
```

## Usage

- Interact with the AI-SQL agent via CLI or HTTP API if provided by the project.
- Provide natural-language prompts and the agent will return a suggested SQL query and explanation.
- Review and (optionally) run the generated SQL against your configured database.

### Example prompt

"Show total monthly revenue for 2025 grouped by product category."

The agent should return a SQL query, an explanation of the query, and (if enabled) the query results.

## Project structure (example)

- src/ - TypeScript source code for the agent and API
- python/ or scripts/ - Python utilities, model runners, or helpers
- web/ - frontend (if present)
- README.md - this file
- .env.example - example environment variables (create one if missing)

## Testing

Run tests (if present):

```bash
npm test
# or
pnpm test
```

## Contributing

Contributions welcome. Please:
1. Fork the repo
2. Create a feature branch
3. Open a Pull Request with a clear description

Provide issue templates and contribution guidelines if you want contributors to follow a specific process.

## Security

- Never commit secrets or API keys. Use .env and add it to .gitignore.
- Review generated SQL before running against production databases.

## License

Add a LICENSE file to the repository and indicate the license here. If you don't have one yet, you can use MIT:

MIT License — see LICENSE file.

## Contact

Repository: https://github.com/OmAmar106/AI-SQL-Agent

---

Notes
- This README is a starting point. Edit the install, run, and usage sections to match the exact scripts and commands used in your repository.