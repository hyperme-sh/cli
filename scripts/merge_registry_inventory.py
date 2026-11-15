"""Join tagged inventory and prior publication-log digests; always rescan."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]

def merge(directory, records):
    rows = {}
    for kind in ('runtime',):
        value = (directory/kind).read_text().strip()
        if not value.startswith('matrix='): raise ValueError('Missing registry inventory')
        for row in json.loads(value.removeprefix('matrix='))['include']:
            rows[(row['repository'],row['digest'])] = row
    for row in records['images']:
        if not re.fullmatch(r'https://github.com/hyperme-sh/hypermesh-cli/actions/runs/[0-9]+',row['run_url']):
            raise ValueError('Invalid originating publication run')
        rows.setdefault((row['repository'],row['digest']),dict(repository=row['repository'],digest=row['digest'],tags=[]))
    for repo,digest in rows:
        if repo not in {'hyperme-sh/hypermesh-cli/runtime'} or not re.fullmatch(r'sha256:[0-9a-f]{64}',digest):
            raise ValueError('Invalid review target')
    if not 1 <= len(rows) <= 256: raise ValueError('Invalid matrix size')
    return list(rows.values())

if __name__ == '__main__':
    rows=merge(Path(sys.argv[1]),json.loads((ROOT/'.github/workflows/recorded-images.json').read_text()))
    print('SELECTED_IMAGE_REVIEWS='+json.dumps(rows,sort_keys=True))
    with Path(sys.argv[2]).open('a') as stream:
        stream.write('matrix='+json.dumps({'include':rows})+'\nreview-needed=true\n')
