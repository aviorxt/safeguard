import importlib.util
from pathlib import Path
import unittest
import tempfile
import json
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('builder',Path(__file__).resolve().parents[1]/'scripts/build.py')
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

class BuilderTests(unittest.TestCase):
    def test_normalization(self):
        self.assertEqual(b.parse('! comment\n||Ads.Example.COM^\n||ads.example.com^'),{'ads.example.com'})
        self.assertEqual(b.domain('bücher.de'),'xn--bcher-kva.de')
    def test_reject_unsafe_syntax(self):
        for rule in ['com','co.uk','127.0.0.1','https://example.com/x','||example.com^$important','@@||example.com^','example.com##.ad','a..com','localhost','x.invalid']:
            with self.subTest(rule=rule),self.assertRaises(ValueError):
                b.parse(rule)
    def test_allowlist_consistency(self):
        result,suppressed=b.apply_allow({'example.com','ads.example.com','bad.com','notexample.com'},{'ads.example.com'})
        self.assertEqual(result,{'bad.com','notexample.com'})
        self.assertEqual(set(suppressed),{'example.com','ads.example.com'})
    def test_allowlist_descendants(self):
        result,_=b.apply_allow({'a.example.com','bad.com'},{'example.com'})
        self.assertEqual(result,{'bad.com'})
    def test_hosts_source_and_audited_exclusion(self):
        self.assertEqual(b.parse('0.0.0.0 ads.example.com'),{'ads.example.com'})
        result,excluded=b.parse_source(('0.0.0.0 good.example.com\n'*200)+'0.0.0.0 not_portable.example.com',{'exclude_invalid_hostnames':True})
        self.assertEqual(result,{'good.example.com'})
        self.assertEqual(excluded[0]['line'],201)
        with self.assertRaises(ValueError):
            b.parse_source('||example.com^',{'exclude_invalid_hostnames':True})
    def test_categories_and_formats_remain_consistent(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'rules').mkdir()
            (root/'rules/allow.txt').write_text('');(root/'rules/block.txt').write_text('')
            (root/'rules/ads-trackers.txt').write_text('extra-ads.example.com')
            (root/'rules/adult.txt').write_text('adult.example.com')
            (root/'catalog.json').write_text(json.dumps([{'id':x,'name':x} for x in ['family','standard','gambling']]))
            (root/'sources.json').write_text(json.dumps([{'id':'privacy','url':'privacy','minimum':1,'profiles':['family','standard']},{'id':'gambling','url':'gambling','minimum':1,'profiles':['gambling']}]))
            with patch.object(b,'ROOT',root),patch.object(b,'download',side_effect=lambda url: b'||ads.example.com^' if url=='privacy' else b'||bets.example.com^'):
                b.build()
            self.assertNotIn('bets.example.com',(root/'blocklists/family.txt').read_text())
            self.assertIn('bets.example.com',(root/'blocklists/gambling.txt').read_text())
            self.assertIn('extra-ads.example.com',(root/'blocklists/standard.txt').read_text())
            self.assertNotIn('adult.example.com',(root/'blocklists/standard.txt').read_text())
            self.assertIn('adult.example.com',(root/'blocklists/family.txt').read_text())
            self.assertNotIn('extra-ads.example.com',(root/'blocklists/gambling.txt').read_text())
            self.assertNotIn('adult.example.com',(root/'blocklists/gambling.txt').read_text())
            self.assertIn('local=/ads.example.com/',(root/'blocklists/family-dnsmasq.conf').read_text())
            self.assertIn('local-zone: "ads.example.com" always_nxdomain',(root/'blocklists/family-unbound.conf').read_text())
            self.assertIn('*.ads.example.com CNAME .',(root/'blocklists/family-rpz.zone').read_text())
    def test_failed_source_preserves_published_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'catalog.json').write_text('[{"id":"family","name":"Family"}]')
            (root/'blocklists').mkdir()
            published=root/'blocklists/family.txt'
            published.write_text('previous valid publication')
            (root/'sources.json').write_text(json.dumps([{'id':'normal','url':'https://example.com','minimum':2,'profiles':['family']}]))
            with patch.object(b,'ROOT',root),patch.object(b,'download',return_value=b'||only.example.com^'):
                with self.assertRaises(ValueError):
                    b.build()
            self.assertEqual(published.read_text(),'previous valid publication')
    def test_unexpected_shrink_preserves_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'catalog.json').write_text('[{"id":"family","name":"Family"}]')
            (root/'sources').mkdir()
            previous=root/'sources/normal.txt'
            previous.write_text('||one.example.com^\n||two.example.com^\n||three.example.com^\n')
            (root/'sources.json').write_text(json.dumps([{'id':'normal','url':'https://example.com','minimum':1,'profiles':['family']}]))
            with patch.object(b,'ROOT',root),patch.object(b,'download',return_value=b'||one.example.com^'):
                with self.assertRaises(ValueError):
                    b.build()
            self.assertIn('three.example.com',previous.read_text())

if __name__=='__main__':
    unittest.main()
