import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import unittest
import io
import json
import os
import tempfile
from unittest.mock import patch
import accept_submission as acceptance
from community import validate, targets

class CommunityTests(unittest.TestCase):
    def entry(self,**changes):
        return {'domain':'ads.example.com','category':'adult','username':'contributor','issue':12,'accepted_utc':'2026-11-04T12:00:00+00:00',**changes}

    def test_scope_preserves_optional_categories(self):
        self.assertEqual(targets('adult'),{'adult','family'})
        self.assertEqual(targets('gambling'),{'gambling'})
        self.assertEqual(targets('malware'),{'malware','threats','standard','family'})

    def test_reject_malformed_attribution_and_inputs(self):
        catalog=[{'id':'adult'}]
        self.assertEqual(len(validate([self.entry()],catalog)),1)
        for changes in [{'domain':'https://bad.com/a'},{'username':'<script>'},{'issue':True},{'category':'standard'},{'accepted_utc':'2026-11-04T12:00:00'}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                validate([self.entry(**changes)],catalog)
        with self.assertRaises(ValueError):
            validate([self.entry(),self.entry()],catalog)

    def test_submission_rejects_spoofing_and_non_maintainers(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            event={'sender':{'login':'maintainer'},'issue':{'number':12}}
            event_path=root/'event.json';event_path.write_text(json.dumps(event))
            issue={'state':'open','labels':[{'name':'approved-domain'}],'user':{'login':'real-author'},'number':12,'body':'### GitHub username\n\nsomeone-else\n\n### Category\n\nadult\n\n### Domain\n\nadult.example.com'}
            env={'GITHUB_EVENT_PATH':str(event_path),'GITHUB_REPOSITORY':'owner/repo','GH_TOKEN':'test-placeholder'}
            for permission,expected in [('read','Only maintainers'),('write','authenticated issue author')]:
                replies=[io.BytesIO(json.dumps({'permission':permission}).encode()),io.BytesIO(json.dumps(issue).encode())]
                with patch.dict(os.environ,env),patch.object(acceptance.urllib.request,'urlopen',side_effect=replies),self.assertRaisesRegex(ValueError,expected):
                    acceptance.main()
