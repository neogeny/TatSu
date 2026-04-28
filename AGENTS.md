---
apply: always
---

# AGENTS

## Project Overview
**TatSu** is PEG parser generator in Python.

## Context

* **Research Phase:** Study [README.rst](README.rst). Read all `*.rst` documents in [./docs/](./docs/) to establish PEG/TatSu domain context.
* **Context Gathering:** Analyze the current Python project structure.
* **Source Mapping:** Cross-reference the Python source in [./tatsu/](./tatsu/) and [./tests/](./tests/).


## Core Operational Rules

* **Code Modification:** Do not use `sed` or `awk` for bulk directory/glob modifications. Target specific files one-by-one only when structural tools are insufficient.
* **Shared Understanding:** You will interview the User relentlessly about every aspect of a plan until it is certain that there is a shared understanding. Walk down each branch of the possible design tree resolving dependencies between decisions one-by-one.
* **Planning**: Formulate a plan and present it to the User before attempting any changes.
* **Ownership of the Assets:** The User is the sole owner of files and other assets. Never modify any file or asset without the explicit consent from the User.
* **Strict Compliance:** Adhere strictly to all the rules specified in the mentioned documents.
* **Rules**: Study [RULES.md](RULES.md), if present, for more detailed guidelines.

## Development Workflow

There is a [Justfile](Justfile) defined for the project with targets for common, version control, and integration. The Python environment is managed using `uv`.
