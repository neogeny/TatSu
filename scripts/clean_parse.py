from pathlib import Path
import re


def main():
    paths = Path('.').glob('test/**/*.py')
    for p in paths:
        text = p.read_text()
        if '._parse(' not in text:
            continue

        print(type(p).__name__)
        print(text)
        print('---')
        new_text = re.sub(r'\._parse\(', '.parse(', text)
        print(new_text)
        p.write_text(new_text)
        return



if __name__ == '__main__':
    main()
