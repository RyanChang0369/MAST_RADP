import unittest, hashlib
from pathlib import Path
import gemini_workflow as workflows

class ConsolidationTests(unittest.TestCase):
    def test_explicit_modes(self):
        self.assertEqual(len(workflows.get_mode("four_category").DEFINITIONS), 4)
        for name in ("fourteen_category", "full_v1", "evidence_v2", "evidence_v2_recovery"):
            self.assertEqual(len(workflows.get_mode(name).DEFINITIONS), 14)
        with self.assertRaises(ValueError): workflows.get_mode("implicit")
    def test_historical_source_hashes(self):
        root = Path(workflows.__file__).parent
        workflows.restore_historical_sources(root)
        for info in workflows.PROVENANCE.values():
            self.assertEqual(hashlib.sha256((root/Path(info["archive"].replace(chr(92), "/"))).read_bytes()).hexdigest(), info["source_sha256"])
    def test_all_modes_deny_api_even_with_allow_api(self):
        workflows.set_api_enabled(False)
        for name in workflows.MODES:
            with self.assertRaises(RuntimeError): workflows.get_mode(name).evaluate(Path('.'), {}, allow_api=True)
    def test_recovery_preserves_prompt_and_schema(self):
        original=workflows.get_mode("evidence_v2"); recovery=workflows.get_mode("evidence_v2_recovery")
        self.assertEqual(original.prompt_for('synthetic trace'),recovery.prompt_for('synthetic trace'))
        self.assertEqual(original.schema(), recovery.schema())

    def test_v3_revision_preserves_trace_schema_and_guards(self):
        v2=workflows.get_mode("evidence_v2"); v3=workflows.get_mode("evidence_v3")
        trace="Synthetic trace with original 'single' and \"double\" quotation marks."
        self.assertIn(trace,v3.prompt_for(trace))
        self.assertEqual(v2.schema(),v3.schema())
        self.assertIn("A browser crash",v3.prompt_for(trace))
        self.assertIn("truncated user-task header",v3.prompt_for(trace))
        self.assertIn("Each quotes array must contain unique strings",v3.prompt_for(trace))
        self.assertNotEqual(v2.prompt_for(trace),v3.prompt_for(trace))
