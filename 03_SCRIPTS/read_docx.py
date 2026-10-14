import sys, docx
d = docx.Document(sys.argv[1])
for i, p in enumerate(d.paragraphs):
    t = p.text.strip()
    if t:
        print(f"[P{i}] {t}")
for ti, tbl in enumerate(d.tables):
    print(f"\n=== TABLE {ti} ({len(tbl.rows)}x{len(tbl.columns)}) ===")
    for r in tbl.rows:
        print(" | ".join(c.text.strip().replace("\n"," ") for c in r.cells))
print("\n--- INLINE IMAGES ---")
import zipfile
z = zipfile.ZipFile(sys.argv[1])
for n in z.namelist():
    if n.startswith("word/media/"):
        print(n, z.getinfo(n).file_size)
