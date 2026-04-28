---
apply: always
---

# Rules

## Interaction

- Never change files without a plan and user authorization
- Never use a Git command that alters files or their version control status.
- Never change more than the files explicitly named in the authorization
- Always consult with the User before making changes that impact multiple files
- Evaluate changes before applying them (no "apply and see" approach)
- Do not act on assumptions. Always verify assumptions with the User.

## Code Tools

- Do not use `sed`, `awk`, or similar text tools to modify code
- Create `./tmp/` for temporary files instead of using `/tmp`
- Never try to access or modify a file or directory outside the current
  project's directory
