---
name: Python dependency installation
description: Project-local Python dependency behavior in the Replit uv environment.
---

Use the project-local `uv` dependency workflow when the Replit package installer falls back to an externally managed system Python. Keep the project dependency metadata and lockfile authoritative, and mirror runtime dependencies in `requirements.txt` when the project exposes that file.

**Why:** The system Python is immutable and can reject pip-based installs even when the project already has a local uv environment.

**How to apply:** Prefer the package-management skill first; if its pip path is blocked by the externally managed environment, use the existing project-local uv workflow rather than bypassing the guard.