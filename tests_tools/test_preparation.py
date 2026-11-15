import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class PreparationTests(unittest.TestCase):
    def test_layer_traversal_and_root_user_are_rejected(self):
        inspect = load('inspect-container')
        for member, user in [('../escape', '65532:65532'), ('safe', '')]:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                layer = io.BytesIO()
                with tarfile.open(fileobj=layer, mode='w') as archive:
                    entry = tarfile.TarInfo(member);entry.size=1
                    archive.addfile(entry, io.BytesIO(b'x'))
                with tarfile.open(root/'image.tar', 'w') as archive:
                    for name, data in {'layer.tar':layer.getvalue(), 'manifest.json':b'[{"Config":"config.json","Layers":["layer.tar"]}]', 'config.json':json.dumps({'config':{'User':user}}).encode()}.items():
                        entry=tarfile.TarInfo(name);entry.size=len(data);archive.addfile(entry,io.BytesIO(data))
                with self.assertRaises(ValueError):
                    inspect.unpack_image(root/'image.tar', root/'out')
                self.assertFalse((root/'escape').exists())

    def test_shallow_history_refused(self):
        module=load('review-history')
        with patch.object(module, 'git', return_value=b'true\n'):
            with self.assertRaises(ValueError):module.review(Path('/unused'))

    def test_notice_inventory_cannot_silently_lose_dependency(self):
        module=load('prepare-notices')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'licenses').mkdir()
            (root/'licenses/modules.json').write_text('[]')
            with patch.object(module.subprocess,'check_output',return_value=b'{"Require":[{"Path":"example.com/a","Version":"v1.0.0"}]}'):
                with self.assertRaises(ValueError):module.prepare(root,root/'out')

    def test_json_stream_handles_multiple_modules(self):
        self.assertEqual(list(load('prepare-notices').documents(' {"a":1}\n {"b":2}')), [{'a':1},{'b':2}])

    def test_pr_has_no_publication_and_no_artifacts(self):
        source=(ROOT/'.github/workflows/container.yml').read_text()
        preparation=source.split('  preparation:',1)[1].split('  publication:',1)[0]
        self.assertNotIn('packages: write',preparation)
        self.assertNotIn('publish-test-container',preparation)
        self.assertIn("github.event_name == 'push' && github.ref == 'refs/heads/main'",source)
        for path in (ROOT/'.github/workflows').glob('*.yml'):
            self.assertNotIn('upload-artifact',path.read_text())
            self.assertNotIn('download-artifact',path.read_text())

    def test_notice_bytes_cannot_change(self):
        import hashlib
        module=load('prepare-notices')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);upstream=root/'cache';upstream.mkdir()
            (upstream/'LICENSE').write_bytes(b'original')
            folder=root/'licenses/dependencies/example.com/module';folder.mkdir(parents=True)
            (folder/'LICENSE').write_bytes(b'changed')
            (root/'licenses/modules.json').write_text(json.dumps([{'module':'example.com/module','version':'v1.0.0','files':{'LICENSE':hashlib.sha256(b'original').hexdigest()}}]))
            outputs=[b'{"Require":[{"Path":"example.com/module","Version":"v1.0.0"}]}',json.dumps({'Path':'example.com/module','Version':'v1.0.0','Dir':str(upstream)}).encode()]
            with patch.object(module.subprocess,'check_output',side_effect=outputs), patch.object(module.subprocess,'run'):
                with self.assertRaisesRegex(ValueError,'notice bytes changed'):module.prepare(root,root/'out')

    def test_publisher_rejects_pr_or_changed_image(self):
        import os
        import subprocess
        fake='''
gh() { printf '%s\\n' "$GITHUB_SHA"; }
docker() {
 case "$1 $2" in
 'image inspect')
 if [[ "$*" == *org.opencontainers.image.revision* ]]; then printf '%s\\n' "$GITHUB_SHA";
 else printf '%s\\n' "$IMAGE_ID"; fi ;;
 'login '*) cat >/dev/null ;;
 'push '*) printf '%s\\n' "$2" >> "$CALLS" ;;
 *) : ;;
 esac
}
'''
        for event,identity,success in [('pull_request','sha256:a',False),('push','sha256:b',False),('push','sha256:a',True)]:
            with self.subTest(event=event,identity=identity), tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                env=dict(os.environ,GITHUB_SHA='a'*40,GITHUB_REPOSITORY='Example/CLI',QUALIFIED_REF='cli:fixture',QUALIFIED_ID='sha256:a',IMAGE_ID=identity,GITHUB_EVENT_NAME=event,GITHUB_REF='refs/heads/main',GH_TOKEN='fixture',GITHUB_ACTOR='fixture',DOCKER_CONFIG=str(root/'login'),GITHUB_STEP_SUMMARY=str(root/'summary'),CALLS=str(root/'calls'))
                result=subprocess.run(['bash','-c',fake+(ROOT/'scripts/publish-test-container.sh').read_text()],env=env,capture_output=True)
                self.assertEqual(result.returncode==0,success)
                self.assertEqual((root/'calls').exists(),success)
