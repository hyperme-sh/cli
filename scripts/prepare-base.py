"""Bind Debian sources and legal texts to the reviewed static base layers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
HOSTS={'deb.debian.org','snapshot.debian.org','codeload.github.com'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def records(manifest):
    return [a for p in manifest['packages'] for a in p['archives']]+[manifest['recipe_reference']]


def validate(manifest):
    if manifest['schema_version']!=1 or manifest['publication_cleared'] is not False:
        raise ValueError('Unexpected source policy')
    seen=set()
    for row in records(manifest):
        u=urllib.parse.urlsplit(row['url'])
        if (Path(row['filename']).name!=row['filename'] or row['filename'] in seen
            or u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password
            or u.port not in (None,443) or u.query or u.fragment
            or not re.fullmatch('[0-9a-f]{64}',row['sha256']) or not 0<row['size']<20*1024*1024):
            raise ValueError('Invalid source record')
        seen.add(row['filename'])
    for p in manifest['packages']:
        if not re.fullmatch('[a-z0-9][a-z0-9+-]*',p['package']):raise ValueError('Invalid package name')
        if p['copyright_source']['archive'] not in {a['filename'] for a in p['archives']}:
            raise ValueError('Missing copyright source')


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('Source redirects require review')


def fetch(manifest, output):
    validate(manifest);output.mkdir(parents=True,exist_ok=False)
    opener=urllib.request.build_opener(NoRedirects())
    for row in records(manifest):
        with opener.open(row['url'],timeout=60) as response:
            data=response.read(row['size']+1)
        if len(data)!=row['size'] or sha(data)!=row['sha256']:raise ValueError('Source bytes changed: '+row['filename'])
        (output/row['filename']).write_bytes(data)
    (output/'index.json').write_text(json.dumps(manifest,indent=2)+'\n')
    verify_sources(manifest,output)


def verify_sources(manifest, directory):
    validate(manifest)
    for row in records(manifest):
        data=(directory/row['filename']).read_bytes()
        if len(data)!=row['size'] or sha(data)!=row['sha256']:raise ValueError('Bundled source changed')
    recipe=manifest['recipe_reference']
    with tarfile.open(directory/recipe['filename']) as archive:
        member=archive.getmember(recipe['package_lock_member'])
        if not member.isfile() or member.size>5*1024*1024:raise ValueError('Invalid recipe package lock')
        lock=json.load(archive.extractfile(member))
    for row in manifest['packages']:
        candidates=[p for p in lock['packages'] if p['name']==row['package'] and p['arch']=='amd64']
        if len(candidates)!=1 or candidates[0]['version']!=row['version']:raise ValueError('Recipe package version mismatch')
        source=row['copyright_source']
        with tarfile.open(directory/source['archive']) as archive:
            member=archive.getmember(source['member'])
            if not member.isfile() or member.size>1024*1024:raise ValueError('Invalid copyright source member')
            data=archive.extractfile(member).read()
        if sha(data)!=row['copyright_sha256']:raise ValueError('Source copyright mismatch')


def verify_layers(manifest,layers):
    config=json.loads((layers/'image-config.json').read_text())
    count=len(manifest['diff_ids'])
    if config['rootfs']['diff_ids'][:count]!=manifest['diff_ids']:raise ValueError('Base layers changed')
    found={}
    for path in layers.glob('*/var/lib/dpkg/status.d/*'):
        if path.name.endswith('.md5sums'):continue
        if path.name in found:raise ValueError('Package status overridden')
        found[path.name]=path
    if set(found)!={r['package'] for r in manifest['packages']}:raise ValueError('Base package inventory changed')
    for row in manifest['packages']:
        status=found[row['package']].read_bytes()
        if sha(status)!=row['status_sha256']:raise ValueError('Installed package status changed')
        values=dict(line.split(': ',1) for line in status.decode().splitlines() if ': ' in line and not line.startswith(' '))
        if values['Version']!=row['version']:raise ValueError('Package version differs from source')
        legal=list(layers.glob('*/usr/share/doc/'+row['package']+'/copyright'))
        if len(legal)!=1 or sha(legal[0].read_bytes())!=row['copyright_sha256']:raise ValueError('Installed copyright changed')
    print(json.dumps({'base_packages':len(found),'verified_base_layers':count,'publication_cleared':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['fetch','verify']);parser.add_argument('directory',type=Path);parser.add_argument('--layers',type=Path)
    args=parser.parse_args();manifest=json.loads((ROOT/'licenses/base-image.json').read_text())
    if args.mode=='fetch':fetch(manifest,args.directory)
    else:
        verify_sources(manifest,args.directory)
        verify_layers(manifest,args.layers)
