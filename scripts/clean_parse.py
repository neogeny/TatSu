from pathlib import Path


def main():
    paths = Path('.').glob('tatsu/**/*.py')
    for p in paths:
        text = p.read_text()
        if text == '':
            continue
        if '->' in text:
            continue
        if 'typing' in text:
            continue

        print(p)


if __name__ == '__main__':
    main()
