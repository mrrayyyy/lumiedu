---
name: auto-commit
description: Stage all changes and create a concise commit message
---

You are an AI acting as a senior engineer.

Your task:
1. Stage all current git changes
2. Analyze the diff
3. Generate a short, clear commit message
4. Commit the changes

Commit message rules:
- Very concise (max 1 sentence)
- Clearly describe WHAT was changed (behavior-level, not code-level)
- No fluff words
- Use present tense
- English only
- Do NOT mention file names
- Do NOT mention implementation details

Preferred structure:
<type>(optional-scope): short description

Allowed types:
feat, fix, refactor, perf, docs, chore, test

If scope is obvious, include it (e.g. auth, ui, api, market).

Now execute:
- git add .
- git commit -m "<generated message>"
