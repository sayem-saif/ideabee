import re
from pathlib import Path

ROOT = Path('.')
PATTERNS = [
    re.compile(r'sk-([A-Za-z0-9]{30,})'),
    re.compile(r'hf_[A-Za-z0-9_-]{20,}'),
    re.compile(r'OPENROUTER_API_KEY'),
    re.compile(r'TAVILY_API_KEY'),
]

def scan():
    matches = []
    for path in ROOT.rglob('*'):
        if path.is_file() and path.suffix not in ('.pyc', '.pyo'):
            try:
                text = path.read_text(errors='ignore')
            except Exception:
                continue
            for pat in PATTERNS:
                for m in pat.finditer(text):
                    snippet = text[max(0, m.start()-40):m.end()+40].replace('\n',' ')
                    matches.append((str(path), m.group(0), snippet))
    return matches


if __name__ == '__main__':
    hits = scan()
    if not hits:
        print('No obvious secret patterns found.')
    else:
        print('Potential secrets found:')
        for path, token, context in hits:
            print(f'- {path}: {token}\n  {context}\n')
