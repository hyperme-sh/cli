"""Check committed notices against the checksum-verified Go module cache."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def documents(text):
    decoder = json.JSONDecoder()
    while text.strip():
        row, end = decoder.raw_decode(text.lstrip())
        text = text.lstrip()[end:]
        yield row


def prepare(root, output):
    records = json.loads((root/'licenses/modules.json').read_text())
    declared = json.loads(subprocess.check_output(['go', 'mod', 'edit', '-json'], cwd=root))['Require']
    if {(r['module'], r['version']) for r in records} != {(r['Path'], r['Version']) for r in declared}:
        raise ValueError('Declared dependency notice inventory changed')
    modules = {r['Path']: r for r in documents(subprocess.check_output(['go', 'mod', 'download', '-json', 'all'], cwd=root).decode())}
    subprocess.run(['go', 'mod', 'verify'], cwd=root, check=True)
    output.mkdir(parents=True, exist_ok=False)
    for row in records:
        module = modules[row['module']]
        if module.get('Version') != row['version'] or 'Error' in module:
            raise ValueError('Downloaded module differs')
        source = Path(module['Dir'])
        expected = {p.name for p in source.iterdir() if p.is_file() and any(word in p.name.lower() for word in ('license', 'copying', 'notice'))}
        if expected != set(row['files']) or not expected:
            raise ValueError('Upstream legal-file inventory changed: '+row['module'])
        for filename, digest in row['files'].items():
            if Path(filename).name != filename:
                raise ValueError('Unsafe notice filename')
            data = (source/filename).read_bytes()
            committed = root/'licenses/dependencies'/row['module']/filename
            if hashlib.sha256(data).hexdigest() != digest or committed.read_bytes() != data:
                raise ValueError('Upstream notice bytes changed: '+row['module'])
        shutil.copytree(root/'licenses/dependencies'/row['module'], output/'dependencies'/row['module'])
    for name in ('LICENSE', 'NOTICE'):
        shutil.copyfile(root/name, output/name)
    goroot = Path(subprocess.check_output(['go', 'env', 'GOROOT']).decode().strip())
    data = (goroot/'LICENSE').read_bytes()
    (output/'GO-LICENSE').write_bytes(data)
    index = {'modules': records, 'go_version': subprocess.check_output(['go', 'version']).decode().strip(),
             'go_license_sha256': hashlib.sha256(data).hexdigest()}
    (output/'index.json').write_text(json.dumps(index, indent=2)+'\n')
    print('Verified notices for '+str(len(records))+' modules and the Go toolchain')


if __name__ == '__main__':
    prepare(Path(__file__).resolve().parents[1], Path(sys.argv[1]))
