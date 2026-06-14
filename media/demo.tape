# Set the output file and terminal styling
Output media/demo.gif

Set Framerate 24
Set Width  1024
Set Height  800

Set Theme "nord"
# Set Theme "Catppuccin Mocha"

# Set Margin 40
# Set MarginFill "#2e3440"

# Set FontFamily "Fira Code"
Set FontSize 20

# Set Shell "/bin/bash --noprofile --norc"
Set Shell "xonsh"

Set TypingSpeed 20ms
Type "uv run tatsu run ./grammar/java.ebnf datasets/*.java --verbose -o gtmp/t.jsonl"
Enter

# Simulate the 8-second processing time
Sleep 2s
# Type "..."
Sleep 2s
# Type " processing..."
Sleep 4s

# Show the output completion
# Type "Done.
# Enter
Sleep 4s
Sleep 4s
