"""Verify that every file path referenced in the project's markdown actually exists.

    python 00_PROJECT_CONTROL/check_links.py

Checks backtick-quoted paths and markdown links that look like project files. Exits 1
if any reference is broken, so it can be used as a validation gate.
"""
import io
import os
import re
import sys

SEP = chr(92)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.git', '__pycache__', 'state'}

# things that look like paths but are not project files
IGNORE = re.compile(
    r'^(https?:|mailto:|#|\$|%|<|C:|/c/)'
    r'|^[A-Z_]+$'
    r'|^\d'
    # shell commands, not paths
    r'|^(python|git|cd|pip|node|npm|powershell) '
    # paths outside this project, cited as provenance
    r'|^(Downloads/|word/|Weekly_Top_Moving|eBay_|Automation/|Competitor_)'
)
FILEISH = re.compile(r'[A-Za-z0-9_.()\- /]+\.(md|py|json|html|sql|ps1|png|docx|txt|db)$')


def candidates(text):
    """Only real paths are validated.

    A backticked bare filename (`run.py`, `BUSINESS_RULES.md`) is a reference by name in
    prose, not a link, so it is not checked - otherwise every mention of a command or a
    sibling document would be reported as broken. A path containing a directory
    separator, or a markdown link target, IS a navigable reference and must resolve.
    """
    out = set()
    for m in re.finditer(r'`([^`\n]+)`', text):
        c = m.group(1).strip()
        if '/' in c:                       # e.g. 06_EVIDENCE/foo.md or ../02_DISCOVERY/x.md
            out.add(c)
    for m in re.finditer(r'\]\(([^)\s]+)\)', text):
        out.add(m.group(1).strip())
    return out


def main():
    broken, checked = [], 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith('.md'):
                continue
            src = os.path.join(dirpath, fn)
            text = io.open(src, encoding='utf-8', errors='replace').read()
            for c in candidates(text):
                if IGNORE.search(c) or not FILEISH.match(c):
                    continue
                if c.endswith('/'):
                    continue
                checked += 1
                target = os.path.normpath(os.path.join(dirpath, c))
                if not os.path.exists(target):
                    # also accept a path given from the project root
                    if os.path.exists(os.path.normpath(os.path.join(ROOT, c))):
                        continue
                    broken.append((os.path.relpath(src, ROOT).replace(SEP, '/'), c))

    print(f'checked {checked} file references across the project markdown')
    if broken:
        print(f'\n{len(broken)} BROKEN reference(s):')
        for s, c in sorted(set(broken)):
            print(f'  {s}  ->  {c}')
        return 1
    print('all references resolve')
    return 0


if __name__ == '__main__':
    sys.exit(main())
