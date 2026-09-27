# Code-Fix Agent

An autonomous agent that reads a failing test, diagnoses the bug, writes a fix, and verifies it actually works — no human in the loop.

## What it does

Point it at a Python file and its test suite. It will:
1. Run the test suite and capture the failure
2. Send the broken code + the exact error to Gemini
3. Extract the proposed fix and write it back to the file
4. Re-run the tests to confirm the fix actually works
5. Retry (up to a set limit) if the first fix doesn't resolve it

This isn't a chatbot that explains what's wrong — it's a closed feedback loop that acts, checks its own work, and tries again if it's wrong.

## How it works

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐     ┌───────────┐
│ Run pytest  │ ──▶ │ Test passing?│ ──▶ │ Send to    │ ──▶ │ Extract & │
│             │     │  (stop here) │     │ Gemini     │     │ write fix │
└─────────────┘     └──────────────┘     └────────────┘     └─────┬─────┘
       ▲                                                           │
       └───────────────────────────────────────────────────────────┘
                         re-run test, repeat if still failing (max 3 attempts)
```

The agent uses the test's own error output as its only signal — it never relies on prior knowledge of what the bug "should" be. Each retry, it re-reads the current state of the file, so it's always reasoning from the actual current code, not a stale copy.

## Example run

```
$ python agent.py buggy_code.py test_buggy_code.py

--- Attempt 1 ---
FAILED test_buggy_code.py::test_add_numbers - assert -1 == 5
Sending failure to Gemini...
Fix applied. Re-testing...
Test passed after fix! Fix successful.
```

## Setup

```bash
git clone https://github.com/devflux25/devflux25-code-fix-agent.git
cd devflux25-code-fix-agent
pip install -r requirements.txt
```

Create a `.env` file with your Gemini API key:
```
GEMINI_API_KEY=your_key_here
```

Run it against any Python file + its pytest test file:
```bash
python agent.py <source_file.py> <test_file.py>
```

## Tech stack

- Python
- Gemini API (`gemini-2.5-flash`) for reasoning about failures and generating fixes
- pytest for test execution and pass/fail signals
- `subprocess` for running tests programmatically and capturing output
- Regex for reliably extracting code from LLM responses

## Limitations / what's next

- Currently handles single-function bugs in isolated files — not yet tested on multi-file projects or complex logic
- No safety sandboxing yet — the agent writes directly to the source file (works fine on a test file, would need guardrails before pointing it at production code)
- GitHub PR automation is in progress — next step is having the agent open a real pull request with its fix instead of editing the file locally

## Why this project

Built to go one level deeper than a typical "LLM wrapper" project — this one has a real feedback loop: it acts, observes the result, and decides whether to try again, instead of just answering a single prompt.
