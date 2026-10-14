"""Parse an auto-saved MCP tool-result file holding a single json_agg::text payload."""
import json, sys

def load_payload(path):
    with open(path, encoding='utf-8') as f:
        obj = json.load(f)
    rows = obj['data']['rows']
    assert len(rows) == 1, f'expected 1 row, got {len(rows)}'
    payload = rows[0]['payload']
    return json.loads(payload) if payload else []

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    data = load_payload(src)
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    print(f'rows={len(data)} -> {dst}')
    if data:
        print('keys:', sorted(data[0].keys()))
