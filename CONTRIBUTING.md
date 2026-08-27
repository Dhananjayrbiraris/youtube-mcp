# Contributing to YouTube Studio MCP

Thank you for your interest in contributing to **YouTube Studio MCP**! We welcome bug reports, feature requests, documentation improvements, and code contributions.

---

## Code of Conduct

Please be respectful, constructive, and inclusive when participating in issues and discussions.

---

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/youtube-mcp.git
   cd youtube-mcp
   ```

2. **Set up the virtual environment with `uv`:**
   ```bash
   uv venv
   uv pip install -e .
   uv pip install pytest ruff
   ```

3. **Run the test suite:**
   ```bash
   pytest
   ```

4. **Lint and format code:**
   ```bash
   ruff check .
   ruff format .
   ```

---

## Submitting Pull Requests

1. Create a descriptive branch for your changes:
   ```bash
   git checkout -b feature/my-cool-feature
   ```
2. Commit your changes with clear, concise commit messages.
3. Ensure all tests pass.
4. Push your branch to your fork and open a Pull Request against `main`.

---

## License

By contributing to this project, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
