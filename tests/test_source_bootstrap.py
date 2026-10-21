"""Source-only bootstrap tests: no dataset or API access is required."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import gemini_workflow as workflows

class SourceBootstrapTests(unittest.TestCase):
    def test_restore_without_data_or_network(self):
        with tempfile.TemporaryDirectory() as td, patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden")) as network:
            root=Path(td)
            restored=workflows.restore_historical_sources(root)
            self.assertEqual(len(restored),len(workflows.PROVENANCE))
            self.assertFalse((root/"data").exists())
            for info in workflows.PROVENANCE.values():
                path=root/Path(info["archive"].replace(chr(92),"/"))
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),info["source_sha256"])
            self.assertEqual(workflows.restore_historical_sources(root),[])
            network.assert_not_called()
    def test_differing_existing_witness_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);info=next(iter(workflows.PROVENANCE.values()))
            path=root/Path(info["archive"].replace(chr(92),"/"));path.parent.mkdir(parents=True)
            path.write_text("modified source that must be preserved",encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"refusing overwrite"):
                workflows.restore_historical_sources(root)
            self.assertEqual(path.read_text(encoding="utf-8"),"modified source that must be preserved")
    def test_get_mode_restores_missing_sources_without_notebook_setup(self):
        with tempfile.TemporaryDirectory() as td, patch.object(workflows,"__file__",str(Path(td)/"gemini_workflow.py")), patch.dict(workflows._CACHE,{},clear=True), patch("urllib.request.urlopen",side_effect=AssertionError("Network forbidden")) as network:
            mode=workflows.get_mode("evidence_v3")
            self.assertEqual(len(mode.DEFINITIONS),14)
            self.assertTrue((Path(td)/"backups").exists())
            self.assertFalse((Path(td)/"data").exists())
            network.assert_not_called()
