# Secretsanta

![CI](https://github.com/SeeYou-Man/secretsanta/actions/workflows/ci.yml/badge.svg)
![Codecov](https://codecov.io/gh/SeeYou-Man/secretsanta/branch/main/graph/badge.svg)

Secretsanta Discord Bot

This is a small Discord bot that assigns Secret Santa recipients to members who have a specific role.

Setup (local development)

1. Create a virtual environment (recommended) and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your bot token (this file is included in the repository for example but should NOT be committed with a real token):

```
DISCORD_BOT_TOKEN=your_real_token_here
```

4. Run the bot:

```powershell
python .\SecretSanta.py
```

Notes and security

- Never commit your real token to git or share it publicly. If a token is accidentally published, reset it via the Discord Developer Portal immediately.
- The bot reads the `DISCORD_BOT_TOKEN` environment variable. The `.env` file is supported (via python-dotenv) for easy local testing.

Development and Testing
---------------------

The project includes a test suite using pytest. To run the tests:

```powershell
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_secretsanta.py -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing
```

The test suite includes:
- Unit tests for core functionality
- Integration tests for Discord commands
- Property tests for assignment generation
- Mock Discord objects for testing without a real server

CI runs automatically on GitHub and checks:
1. All tests pass
2. Code style with flake8
3. Simulation tests with various configurations

VS Code debug/run
If you prefer to run or debug from VS Code, the provided `.vscode/launch.json` uses the `.env` file automatically (see the `envFile` entry). Use the Run and Debug view to start the configuration named "Run SecretSanta".

Commands

Basic Usage
- `/secretsanta` - Run Secret Santa on role named `Secret Santa` (default)
- `/secretsanta Role Name` - Run Secret Santa for a custom role name (e.g. `/secretsanta MyRole`)

Exclusion Management
- `/exclude @UserA @UserB` - Add a permanent exclusion so those users will never be assigned to each other (both directions)
- `/remove_exclusion @UserA @UserB` - Remove a previously added exclusion between two users
- `/list_exclusions` - Show all current exclusions

Advanced Assignment Options
- `/circle` - Generate a single-cycle Secret Santa (one big circle) for the role
- `/circle_exclude @UserA @UserB` - Generate a single-cycle assignment while temporarily excluding a specific pair

Notes
- Exclusions are stored in `exclusions.json` and persist across bot restarts
- Order doesn't matter: if A↔B is excluded, both A→B and B→A are prevented
- Duplicate exclusions are automatically prevented
- The bot will report if assignments are impossible due to exclusions

If you want, I can: (a) add `.gitignore` with `.env` if you don't have one, or (b) create a tiny test harness that simulates assignments without sending DMs.
 
I've added a `.gitignore` and a small simulation harness `simulate_assignments.py` that you can run locally to validate the assignment logic without sending any Discord messages.

Deployment
----------

There are several simple ways to host this bot so it's online 24/7. In all cases, store your bot token securely (never commit it).

- GitHub Actions (quick tests): A CI workflow is included at `.github/workflows/ci.yml` which installs dependencies and runs the local simulation as a smoke test. This is not a deployment but is useful for automated checks.

- VPS / Docker: Create a systemd service or Docker container and set the environment variable `DISCORD_BOT_TOKEN` on the host (or use a secrets manager). Example Docker run:

```powershell
docker run -d --name secretsanta -e DISCORD_BOT_TOKEN="${{ secrets.DISCORD_BOT_TOKEN }}" your-image
```

- Platform-as-a-Service (Heroku, Railway, Fly): Use the platform web UI to set the environment variable `DISCORD_BOT_TOKEN` in the project's settings/secrets. Push your code and configure the process to run `python SecretSanta.py`.

Secrets in GitHub
-----------------

If you ever hook up a deployment pipeline from GitHub, don't put the token in the repo. Instead add it to the repository Settings → Secrets → Actions as `DISCORD_BOT_TOKEN`. Your deploy workflow can reference it from secrets.

If you'd like, I can add an example deploy workflow for a specific platform (Heroku, Railway or a simple Docker image + GitHub Actions deploy). Tell me which hosting provider you prefer and I will add a concrete workflow / Dockerfile.
