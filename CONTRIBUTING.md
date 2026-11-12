# Contributing

## Branch and pull-request workflow

1. Start from an up-to-date `main`: `git switch main` then `git pull --ff-only`.
2. Create a focused branch: `git switch -c feat/short-description` (or `fix/` / `docs/`).
3. Make a small change, run the checks below and inspect `git diff --check` and `git diff`.
4. Commit with a descriptive message, push the branch and open a pull request against `main`.
5. Explain the reason, validation results and hardware limitations. Resolve failing checks before merging.

Do not commit credentials, personal recordings, local environments or generated builds. Preserve third-party notices and research provenance. Report a reproducible issue with environment/tool versions before proposing a fix.

## Local checks

Run from the repository root with Python 3.12. Install the listed tools in a virtual environment; system tools must be on PATH.

```sh
python tools/check_repository.py
python -m pip install ruff==0.11.13
ruff check .
```

## What CI establishes

CI checks local Markdown links, source syntax and unresolved merge markers. External links are not polled on every push. Ruff checks syntax and selected correctness rules without requiring hardware libraries. Existing tests depend on model downloads, external services or Pi peripherals; the offline job does not execute those integration tests. Run them explicitly on a configured Pi and record results.

These workflows run on pushes and pull requests with read-only repository permissions and bounded execution time. A green check applies to the checks listed here; it does not establish physical hardware validation.
