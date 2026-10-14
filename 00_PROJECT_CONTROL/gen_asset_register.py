"""Generate ASSET_REGISTER.md from the real filesystem.

Run from the project root:  python 00_PROJECT_CONTROL/gen_asset_register.py

The register is generated, never hand-maintained, so it cannot drift from what is
actually on disk. Re-run it after adding or removing files.
"""
import datetime
import io
import os

SEP = chr(92)          # backslash, kept out of string literals
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {'.git', '__pycache__', 'state', 'logs', '.pytest_cache'}

PURPOSE = {
    '00_PROJECT_CONTROL': 'Project control: start-here, scope, status, asset register',
    '01_REQUIREMENT': 'Requirement register, business rules, open questions',
    '02_DISCOVERY': 'Discovery: data sources, existing assets, duplicate risk, push mapping',
    '02_REFERENCE': 'Source reference material (requirement sample screen)',
    '03_SCRIPTS': 'Analysis, extraction, build and test scripts (dashboard pipeline)',
    '04_DATA': 'Extracted datasets and build inputs/outputs',
    '05_OUTPUT': 'Standalone dashboard HTML versions (v001-v003)',
    '06_EVIDENCE': 'Evidence packs: discovery, validation, live checks, screenshots',
    '07_AUTOMATION': 'Index into automation/ - the code itself is NOT duplicated here',
    '08_VALIDATION': 'Test results, validation checklist, pass/fail report',
    '09_GITHUB': 'Repository, commit and push evidence',
    '09_HANDOVER': 'Superseded by 10_HANDOVER (kept, empty)',
    '10_HANDOVER': 'Handover, remaining work, unknown-developer check',
    '11_DAILY_STATUS': 'Daily status notes',
    '12_PROMPTS': 'Prompt register',
    'automation': 'The daily automation engine (config/sources/engine/history/alerts/publisher/api/run)',
    '(root)': 'Original project documents and repository configuration',
}


def main():
    rows = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        rel = os.path.relpath(dirpath, ROOT).replace(SEP, '/')
        if rel == '.':
            rel = '(root)'
        for fn in sorted(filenames):
            try:
                sz = os.path.getsize(os.path.join(dirpath, fn))
            except OSError:
                continue
            rows.append((rel, fn, sz))

    by_dir = {}
    for d, f, s in rows:
        by_dir.setdefault(d, []).append((f, s))

    o = io.StringIO()
    o.write('# ASSET REGISTER - BBOX\n\n')
    o.write(f'Generated from the filesystem on {datetime.date.today().isoformat()} by\n'
            '`00_PROJECT_CONTROL/gen_asset_register.py`. It is generated, not hand-maintained,\n'
            'so it cannot drift from what is on disk. Re-run after adding or removing files.\n\n')
    o.write(f'**{len(rows)} files across {len(by_dir)} directories.**\n\n')
    o.write('| Directory | Files | Bytes | Purpose |\n|---|---|---|---|\n')
    for d in sorted(by_dir):
        tot = sum(s for _, s in by_dir[d])
        o.write(f'| `{d}` | {len(by_dir[d])} | {tot:,} | {PURPOSE.get(d.split("/")[0], "")} |\n')

    o.write('\n---\n\n## Full inventory\n')
    for d in sorted(by_dir):
        o.write(f'\n### `{d}`\n\n| File | Bytes |\n|---|---|\n')
        for f, s in sorted(by_dir[d]):
            o.write(f'| {f} | {s:,} |\n')

    dst = os.path.join(ROOT, '00_PROJECT_CONTROL', 'ASSET_REGISTER.md')
    io.open(dst, 'w', encoding='utf-8').write(o.getvalue())
    print(f'ASSET_REGISTER.md written: {len(rows)} files, {len(by_dir)} directories')


if __name__ == '__main__':
    main()
