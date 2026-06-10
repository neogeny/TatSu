Terminal Color Escape Codes ReferenceThis document provides the exact ANSI escape sequence structures for 8-bit (256-color) and 24-bit (True Color RGB) terminal text formatting.The base escape prefix is \x1b[ (frequently represented as \e[ or \033[ depending on the programming language).1. 256-Color Palette (8-Bit)Use these sequences to select a color from the terminal's pre-defined 256-color lookup table.Escape FormatForeground Text: \x1b[38;5;<ID>mBackground: \x1b[48;5;<ID>mWhere <ID> is a decimal integer from 0 to 255.Color Map Breakdown0 - 15: Standard system colors (e.g., 31 for red, 32 for green).16 - 231: $6 \times 6 \times 6$ RGB color cube, calculated via:$$16 + 36r + 6g + b \quad (\text{where } r, g, b \in [0, 5])$$232 - 255: Grayscale steps from dark gray to off-white.Quick Example# Foreground text in vibrant orange (ID 208)
printf "\x1b[38;5;208mOrange Text\x1b[0m\n"
2. True Color Palette (24-Bit RGB)Use these sequences to set absolute Red, Green, and Blue intensity values.Escape FormatForeground Text: \x1b[38;2;<R>;<G>;<B>mBackground: \x1b[48;2;<R>;<G>;<B>mWhere <R>, <G>, and <B> are decimal intensity levels from 0 to 255.Quick Example# Foreground text in Teal (R: 0, G: 180, B: 180)
printf "\x1b[38;2;0;180;180mTeal Text\x1b[0m\n"

# White text (37) on a Deep Purple background (R: 90, G: 30, B: 120)
printf "\x1b[48;2;90;30;120;37mPurple Background\x1b[0m\n"
3. Reset SequenceAlways append the reset code to prevent active formatting styles from bleeding into subsequent terminal output.Reset All Attributes: \x1b[0m
