class MultiProgress:
    # ... (thread orchestration remains identical) ...

    def _render_loop(self):
        while self._running:
            with self._lock:
                snapshot = copy.deepcopy(self._bars)

            if not snapshot:
                time.sleep(0.05)
                continue

            try:
                # Use the helper attached to your Color engine
                screen_cols, _ = Color.default().terminal_size()
            except Exception:
                screen_cols = 80

            now = time.time()
            lines = []

            for b in snapshot:
                # 1. Library calculates runtime metrics safely
                elapsed = now - b.start_time
                pct = (b.current / b.total * 100) if b.total > 0 else 0.0
                rate = b.current / elapsed if elapsed > 0 else 0
                eta = (b.total - b.current) / rate if rate > 0 else 0.0

                metrics = {"pct": pct, "elapsed": elapsed, "eta": eta}

                # 2. Collect Style definitions from the component
                styles = b.render(screen_cols, metrics)

                # 3. Calculate fixed width footprint of all plain text strings
                # This ignores ANSI code lengths because Style.__str__ or Style.value
                # yields lengths accurately depending on the policy status.
                fixed_width = sum(len(s.value) for s in styles if s.value != "{bar}")
                bar_budget = max(0, screen_cols - fixed_width)

                # 4. Construct the physical layout line
                line_chunks = []
                for style in styles:
                    if style.value == "{bar}":
                        # Draw the flex component inline using calculated budget
                        fill_len = int(bar_budget * (pct / 100))
                        empty_len = bar_budget - fill_len
                        bar_str = f"[{'█' * fill_len}{'-' * empty_len}]"

                        # Apply parent style configuration to the generated bar block
                        line_chunks.append(style(bar_str))
                    else:
                        # Render the pre-configured styled string block
                        line_chunks.append(str(style))

                lines.append("".join(line_chunks))

            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()

            time.sleep(0.05)  # 20 FPS
            sys.stdout.write(f"\033[{len(snapshot)}A")
