### Rich Markup Specification

Rich markup injects styles into strings using bracketed tags: `[tag]text[/tag]`.

---

### 1. Opening Tags (`[tag]`)

Multiple attributes can be combined inside a single tag using spaces. Order does not matter.

* **Colors:** Names (`[red]`), Hex (`[#ff00ff]`), or RGB (`[rgb(255,0,255)]`).
* **Backgrounds:** Prefix any color with `on ` (`[white on blue]`, `[bold red on #000000]`).
* **Attributes:** `[bold]`, `[italic]`, `[underline]`, `[dim]`, `[reverse]`, `[blink]`.
* **Hyperlinks:** `[link=url]` (e.g., `[link=[https://example.com](https://example.com)]Click[/link]`).

---

### 2. Closing Tags (`[/...]`)

Closing tags unwind styles from right to left using three valid formats:

* **`[/]`**: Pops the most recent single attribute or tag off the style stack.
* **`[/style]`**: Targets and closes one specific attribute or color by name (e.g., `[/bold]`, `[/red]`), leaving other active styles intact.
* **`[/all]`**: Instantly clears all open styles and resets to system default.

---

### 3. Escaping Literal Brackets

* **Rule:** Double the opening bracket to render a literal `[` without triggering the parser.
* **Example:** `[[this is plaintext brackets]]` renders as `[this is plaintext brackets]`.
