import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from datetime import datetime, timezone, timedelta

spec=importlib.util.spec_from_file_location('site_builder',Path(__file__).resolve().parents[1]/'scripts/build_site.py')
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class PublicationTests(unittest.TestCase):
    def fixture(self, root):
        (root/'blocklists').mkdir()
        report={'generated_utc':datetime.now(timezone.utc).isoformat(),'outputs':{},'profiles':{},'sources':[]}
        for profile in ('standard','family'):
            report['profiles'][profile]={'domains':1}
            for suffix,content in (('',b'||ads.example.com^\n'),('-domains',b'ads.example.com\n'),('-hosts',b'0.0.0.0 ads.example.com\n')):
                name=f'blocklists/{profile}{suffix}.txt'
                (root/name).write_bytes(content)
                report['outputs'][name]=hashlib.sha256(content).hexdigest()
        (root/'blocklists/report.json').write_text(json.dumps(report))
        return report

    def test_valid_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.fixture(root)
            self.assertEqual(b.validate(root)['profiles']['family']['domains'],1)

    def test_corrupted_download_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); self.fixture(root)
            (root/'blocklists/family.txt').write_text('corrupt')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                b.validate(root)

    def test_stale_lists_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); report=self.fixture(root)
            report['generated_utc']=(datetime.now(timezone.utc)-timedelta(days=3)).isoformat()
            (root/'blocklists/report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'stale'):
                b.validate(root)

    def test_missing_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); report=self.fixture(root)
            del report['outputs']['blocklists/family.txt']
            (root/'blocklists/report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'manifest'):
                b.validate(root)

if __name__=='__main__':
    unittest.main()
