# Code-Fix Agent

An autonomous agent that reads a failing test, diagnoses the bug, writes a fix, verifies it, and opens a GitHub pull request, with no human in the loop.

**See it in action:** [an example PR opened entirely by the agent](https://github.com/devflux25/devflux25-code-fix-agent/pull/1)

## What it does

Point it at a Python file and its pytest test file. It will:

1. Run the tests and capture the failure output
2. Send the broken code and the exact error to Gemini
3. Extract the proposed fix and write it back to the file
4. Re-run the tests to confirm the fix actually works
5. Retry (up to 3 attempts) if the fix doesn't resolve the failure
6. Once the tests pass, create a new branch, commit the fix, push it, and open a pull request on GitHub with a title and description

This isn't a chatbot that explains what's wrong. It's a closed feedback loop that acts, checks its own work, and tries again if it's wrong, then hands the result to a human for review the way a real contributor would.

## How it works

```
        +-------------+
        | Run pytest  |<-----------------------------+
        +------+------+                              |
               |                                     |
       tests pass already?                           |
        yes /      \ no                              |
           /        \                                |
    (nothing      +--v-----------+   +-------------+ |
     to fix)      | Send code +  |-->| Extract fix | |
                  | error to     |   | and write   |-+
                  | Gemini       |   | to the file |
                  +--------------+   +-------------+
                                     (max 3 attempts)

   Tests pass after a fix
            |
            v
   Create branch -> commit -> push -> open PR via GitHub API
```

A few design decisions worth noting:

- **The test output is the only signal.** The agent has no prior knowledge of what the bug is. It reasons from the failure text alone.
- **It re-reads the file on every attempt.** Each retry works from the current state of the code, never a stale copy.
- **Strict output format.** Gemini is told to return only a fenced code block, and the agent extracts it with a regex, so explanations or extra text around the code can't corrupt the file.
- **No-op runs are skipped.** If the tests already pass, no branch, commit, or PR is created.
- **Bounded retries.** A hard limit of 3 attempts stops the agent from looping forever on a bug it can't fix.
- **Review stays with a human.** The agent opens a PR instead of pushing to `main`, so every change gets reviewed before it's merged.

## Example run

```
$ python agent.py buggy_code.py test_buggy_code.py

FAILED test_buggy_code.py::test_add_numbers - assert 6 == 5

--- Attempt 1 ---
Test passed after fix! Fix successful.

Switched to a new branch 'agent-fix-20260928-223412'
[agent-fix-20260928-223412 d30391f] Agent fix: resolved test failure in buggy_code.py
 1 file changed, 1 insertion(+), 1 deletion(-)
To https://github.com/devflux25/devflux25-code-fix-agent.git
 * [new branch]      agent-fix-20260928-223412 -> agent-fix-20260928-223412

PR status: 201
PR link: https://github.com/devflux25/devflux25-code-fix-agent/pull/1
```

## Setup

```bash
git clone https://github.com/devflux25/devflux25-code-fix-agent.git
cd devflux25-code-fix-agent
pip install -r requirements.txt
```

Create a `.env` file in the project folder with two keys:

```
GEMINI_API_KEY=your_gemini_key
GITHUB_TOKEN=your_github_personal_access_token
```

- Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/).
- Create a GitHub **classic** personal access token with the `repo` scope (GitHub -> Settings -> Developer settings -> Personal access tokens).
- `.env` is listed in `.gitignore`, so your keys are never committed.

Run it against any Python file and its pytest test file:

```bash
python agent.py <source_file.py> <test_file.py>
```

The target file needs to live in a git repository with a GitHub remote named `origin`, since the agent pushes a branch and opens a PR against `main`.

## Tech stack

- **Python**
- **Gemini API** (`gemini-2.5-flash`) for diagnosing failures and generating fixes
- **pytest** for running tests and producing the pass/fail signal
- **subprocess** for running pytest and git commands programmatically
- **Regex** for extracting code from LLM responses
- **GitHub REST API** (via `requests`) for opening pull requests

## Limitations

- Handles small, self-contained bugs (single functions in a single file). It hasn't been tested on multi-file projects or bugs that need wider context.
- Assumes the tests themselves are correct. If a test is wrong, the agent will "fix" the code to satisfy it.
- Writes directly to the source file before committing. Fine for a working branch, but it would need a sandbox or a temporary copy before being pointed at code you can't easily revert.
- The GitHub repo for PR creation is currently hardcoded in `agent.py` instead of being read from the git remote.
- Uses the `google-generativeai` package, which Google has deprecated. Migrating to `google-genai` is planned.

## Roadmap

- Migrate to the `google-genai` SDK
- Detect the repository and default branch automatically from the git remote
- Include the retry history and the agent's reasoning in the PR description
- Support multiple failing tests and multi-file fixes
- Run fixes in a sandbox before touching the working tree

## Why this project

Built to go one level deeper than a typical "LLM wrapper." Most AI projects take an input, call a model once, and show the answer. This one has a real feedback loop: it acts, observes the result, decides whether to try again, and finally takes an action in the outside world by opening a pull request. Every part of the loop was written by hand, without an agent framework.