# **Engineer & Project Context**

This document serves as a persistent context for the collaboration between **Juancarlo Añez** (apalala) and the AI assistant. It outlines the engineer's profile, the primary project, and the specific tasks undertaken.

## 1. The Engineer

**Juancarlo Añez** (apalala) is an experienced software engineer and the creator of the **TatSu** library. He works primarily in a macOS/Linux environment (often using `xonsh`) and values clean, modern, and efficient code.

## 2. The Project: TatSu

**TatSu** is a tool that generates parsers in Python from grammars written in an extended EBNF format. It specializes in creating memoizing (Packrat) PEG parsers, which are essential for understanding the logic and structure of hierarchical data. TatSu is used to create Domain-Specific Languages (DSLs), translate data formats, and handle complex, recursive structures that regular expressions cannot.

*   **Repository**: `neogeny/TatSu`
*   **Key Technologies**: Python, PEG Parsing, Memoization.

---

## 3. Task: `ideps.py` (Module Dependency Analyzer)

**Status**: *Completed (Initial Version)*

This task involved creating a command-line tool (`scripts/ideps.py`) to visualize the internal and external dependencies of Python modules within the TatSu project.

### 3.1. Objective
Generate a visual dependency tree using `rich.tree` that accurately represents the project's structural hierarchy while clearly distinguishing it from various types of import dependencies.

### 3.2. Implementation Logic
The script operates in three phases:
1.  **Structural Skeleton**: Builds a tree of the physical module hierarchy based on qualified names (e.g., `tatsu.contexts._protocol`).
2.  **Dependency Annotation**: Adds imports as leaf nodes, avoiding redundancy if the import is already a structural child.
3.  **Recursive Sorting**: Sorts the tree at every level for consistency.

### 3.3. Visual Grammar & Naming
The output adheres to a strict visual grammar:

| Relationship              | Symbol | Example          | Style | Naming Convention                               |
| ------------------------- | :----: | ---------------- | ----- | ----------------------------------------------- |
| **Structural Node**       |  None  | `contexts`       | `cyan`  | The module's own name.                          |
| **Sibling Import**        |   `○`  | `○ _core`        | `cyan`  | Just the module name (leaf).                    |
| **Uncle Import**          |   `◉`  | `◉ .._protocol`  | `cyan`  | Relative path notation (`..`).                  |
| **Other Internal Import** |   `◉`  | `◉ ast`          | `cyan`  | Path relative to the project root (e.g., `util`). |
| **External Import**       |   `⟨⟩` | `⟨typing⟩`       | `white` | Full qualified name of the external module.     |

**Sorting Order**:
1.  Structural Nodes
2.  Sibling Imports (`○`)
3.  Other Internal Imports (`◉`)
4.  External Imports (`⟨⟩`)

### 3.4. Key Milestones
*   **AST Parsing**: Used `ast` to reliably find imports.
*   **Glob Expansion**: Added internal support for patterns like `tatsu/**/*.py`.
*   **Structure vs. Dependency**: Solved the issue of conflating submodule containment with imports.
*   **Intelligent Naming**: Implemented logic to shorten names based on context (siblings, uncles).
*   **Symbol Differentiation**: Used `○` for siblings and `◉` for other internal imports.
