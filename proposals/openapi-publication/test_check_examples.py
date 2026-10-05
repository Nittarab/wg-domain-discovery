import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent


class CheckExamplesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'proposal'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__', 'build'))

    def run_checker(self, *args):
        return subprocess.run(
            [sys.executable, str(self.root / 'check_examples.py'), *args],
            capture_output=True, text=True,
        )

    def test_valid_examples(self):
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_variants(self):
        cases = [
            ({'accepts': []}, 'minItems'),
            ({'accepts': [{'network': 'eip155:8453'}]}, 'scheme'),
            ({'accepts': [{'scheme': 'exact'}]}, 'network'),
            ({'accepts': [{'scheme': 'exact', 'network': 'eip155:8453',
                          'asset': 'USD', 'minAmount': '1'}]}, 'maxAmount'),
            ({'accepts': [{'scheme': 'exact', 'network': 'eip155:8453',
                          'asset': 'USD', 'minAmount': '10', 'maxAmount': '1'}]},
             'minAmount exceeds maxAmount'),
        ]
        path = self.root / 'examples/annotation-variants.json'
        variants = json.loads(path.read_text())
        for annotation, message in cases:
            with self.subTest(annotation=annotation):
                variants['payment-schemes'] = annotation
                path.write_text(json.dumps(variants))
                result = self.run_checker()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)

    def test_invalid_overlay_annotation(self):
        path = self.root / 'examples/stabletravel.overlay.json'
        overlay = json.loads(path.read_text())
        overlay['actions'][0]['update']['x-x402']['accepts'] = []
        path.write_text(json.dumps(overlay))
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('minItems', result.stderr)

    def test_invalid_inline_annotation(self):
        path = self.root / 'proposal.md'
        path.write_text(path.read_text().replace('"x-x402": {}', '"x-x402": {"accepts": []}'))
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('minItems', result.stderr)

    def test_invalid_generated_annotation(self):
        path = self.root / 'examples/stablestudio.challenge-excerpt.json'
        challenge = json.loads(path.read_text())
        challenge['accepts'][0]['scheme'] = ''
        path.write_text(json.dumps(challenge))
        path = self.root / 'examples/stablestudio.final.openapi.json'
        document = json.loads(path.read_text())
        operation = document['paths']['/api/generate/nano-banana-pro/generate']['post']
        operation['x-x402']['accepts'][0]['scheme'] = ''
        path.write_text(json.dumps(document))
        result = self.run_checker()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stablestudio.final.openapi.json', result.stderr)
        self.assertIn('minLength', result.stderr)

    def test_write_preserves_final_documents(self):
        snapshots = {path: path.read_bytes()
                     for path in (self.root / 'examples').glob('*.final.openapi.json')}
        result = self.run_checker('--write')
        self.assertEqual(result.returncode, 0, result.stderr)
        for path, original in snapshots.items():
            self.assertEqual(json.loads(path.read_bytes()), json.loads(original))
            service = path.name.split('.')[0]
            self.assertEqual((self.root / 'build' / service / 'openapi.json').read_bytes(),
                             path.read_bytes())
            self.assertTrue((self.root / 'build' / service / '.well-known/x402').is_file())


if __name__ == '__main__':
    unittest.main()
