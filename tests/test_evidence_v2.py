"""Offline-only regression tests. Run: python -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import gemini_workflow as workflows
workflow = workflows.get_mode("evidence_v2")


class EvidenceV2Tests(unittest.TestCase):
    def fixture(self):
        return {c: {'decision': 'absent', 'evidence': 'The synthetic record shows a completed action, not this failure.', 'quotes': []} for c in workflow.DEFINITIONS}

    def test_absent_requires_rationale_but_not_quote(self):
        obj = self.fixture()
        parsed = workflow.parse_prediction(json.dumps(obj))
        self.assertTrue(all(x['present'] is False for x in parsed.values()))
        obj['step_repetition']['evidence'] = ''
        with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))

    def test_insufficient_is_not_false(self):
        obj = self.fixture()
        obj['step_repetition']['decision'] = 'insufficient_evidence'
        self.assertIsNone(workflow.parse_prediction(json.dumps(obj))['step_repetition']['present'])

    def test_missing_and_extra_category_rejected(self):
        obj = self.fixture(); del obj['step_repetition']
        with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))
        obj = self.fixture(); obj['extra'] = {}
        with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))

    def test_duplicate_nested_key_rejected(self):
        text = json.dumps(self.fixture()).replace('"decision": "absent"', '"decision": "absent", "decision": "present"', 1)
        with self.assertRaises(ValueError): workflow.parse_prediction(text)

    def test_duplicate_category_rejected(self):
        with self.assertRaises(ValueError): workflow.parse_prediction('{"step_repetition":{},"step_repetition":{}}')

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError): workflow.parse_prediction('{"step_repetition": NaN}')

    def test_unknown_decision_rejected(self):
        obj = self.fixture(); obj['step_repetition']['decision'] = 'no'
        with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))

    def test_wrong_fields_rejected(self):
        obj = self.fixture(); obj['step_repetition']['present'] = False
        with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))

    def test_positive_requires_quotes(self):
        obj = self.fixture(); obj['task_derailment']['decision'] = 'present'
        with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))

    def test_repetition_and_termination_need_two_distinct_spans(self):
        for category in ('step_repetition', 'unaware_of_termination_conditions'):
            obj = self.fixture(); obj[category].update(decision='present', quotes=['one'])
            with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))
            obj[category]['quotes'] = ['one', 'one']
            with self.assertRaises(ValueError): workflow.parse_prediction(json.dumps(obj))
            obj[category]['quotes'] = ['one', 'two']
            workflow.parse_prediction(json.dumps(obj))

    def test_quotes_exact_and_offsets_saved(self):
        obj = self.fixture(); obj['task_derailment'].update(decision='present', quotes=['another task'])
        parsed = workflow.parse_prediction(json.dumps(obj))
        positions = workflow.validate_quotes(parsed, 'This is another task.')
        self.assertEqual(positions['task_derailment'][0]['start_character'], 8)
        with self.assertRaises(ValueError): workflow.validate_quotes(parsed, 'This record lacks that quote.')

    def test_full_trace_preserved(self):
        trace = 'BEGIN_TEST\n' + ('complete original content\n' * 20000) + 'END_TEST'
        self.assertIn(trace, workflow.prompt_for(trace))

    def test_api_guard(self):
        with self.assertRaises(RuntimeError): workflow.evaluate(ROOT, {}, allow_api=False)

    def test_transport_does_not_retry(self):
        client = workflow.GeminiREST('synthetic-not-a-real-key', 'gemini-3.5-flash-lite')
        with patch.object(client.opener, 'open', side_effect=TimeoutError('synthetic')) as call:
            with self.assertRaises(RuntimeError): client.request('generateContent', {})
            self.assertEqual(call.call_count, 1)

    def test_score_abstention_and_repeatability(self):
        obj = self.fixture(); obj['step_repetition']['decision'] = 'insufficient_evidence'
        parsed = workflow.parse_prediction(json.dumps(obj)); h = '0' * 64
        dataset = {'label_origin': 'synthetic', 'references': [{'trace_hash': h, 'category': 'step_repetition', 'label': True}]}
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            workflow.save(folder / (h + '.json'), {'trace_hash': h, 'status': 'valid', 'predictions': parsed})
            first = workflow.score(dataset, folder); second = workflow.score(dataset, folder)
            self.assertEqual(first, second)
            item = next(x for x in first if x['category'] == 'step_repetition')
            self.assertEqual(item['abstentions'], 1)
            self.assertEqual(item['scored'], 0)
            self.assertEqual(item['fn'], 0)
            self.assertEqual(item['decision_coverage'], 0)
            self.assertEqual(item['response_coverage'], 1)

    def test_windows_save_fallback_preserves_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / 'synthetic.json'; target.write_text('{}')
            with patch.object(Path, 'replace', side_effect=PermissionError('synthetic replacement failure')):
                workflow.save(target, {'ok': True})
            self.assertEqual(json.loads(target.read_text()), {'ok': True})
            self.assertEqual(len(list((target.parent / 'recovery_snapshots').glob('*.json'))), 1)


if __name__ == '__main__':
    unittest.main()
