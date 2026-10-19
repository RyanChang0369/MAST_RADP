import unittest, tempfile, json
from pathlib import Path
from unittest.mock import Mock, patch
import gemini_workflow as workflows

class FullBatchTests(unittest.TestCase):
    def setUp(self):
        self.mode=workflows.get_mode("evidence_v3")
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        review=self.root/"data/processed/step6_consolidated_audit/step6_execution_review.json"
        review.parent.mkdir(parents=True);review.write_text(json.dumps({"execution_authorized":True,"classifier_code_sha256":self.mode.RECOVERY_CODE_SHA256}))
        self.hash="f"*64
        self.data={"traces":{self.hash:"Synthetic complete trace"},"dataset_revision":"synthetic","dataset_sha256":"synthetic","split_manifest_sha256":"synthetic","label_origin":"synthetic","references":[]}
        self.pred={c:{"decision":"absent","evidence":"Synthetic task completes with no observed defining failure.","quotes":[]} for c in self.mode.DEFINITIONS}
        self.response={"candidates":[{"finishReason":"STOP","content":{"parts":[{"text":json.dumps(self.pred)}]}}]}
        self.client=Mock()
        self.load=patch.object(self.mode,"load_corpus",return_value=self.data);self.load.start()
        self.transport=patch.object(self.mode,"GeminiREST",return_value=self.client);self.transport.start()
        self.pacing=patch.object(self.mode.Pacer,"before",lambda *a:None);self.pacing.start()
        self.env=patch.dict("os.environ",{"LLM_PROVIDER":"gemini","LLM_MODEL":"gemini-3.5-flash-lite","GEMINI_RPM_LIMIT":"15","GEMINI_INPUT_TPM_LIMIT":"250000","GEMINI_RPD_LIMIT":"500","MAX_INPUT_TOKENS":"225000"});self.env.start()
        workflows.set_api_enabled(True)
    def tearDown(self):
        workflows.set_api_enabled(False);self.env.stop();self.pacing.stop();self.transport.stop();self.load.stop();self.temp.cleanup()
    def test_valid_and_no_repeat_generation(self):
        self.client.request.side_effect=[{"inputTokenLimit":1000000,"outputTokenLimit":8192},{"totalTokens":100},self.response]
        r=workflows.run_step6_batch(self.root,allow_api=True)
        self.assertEqual(r["valid"],1);self.assertEqual(r["generation_requests"],1)
        again=workflows.run_step6_batch(self.root,allow_api=True)
        self.assertEqual(again["generation_requests"],0)
        self.assertEqual(self.client.request.call_count,3)
    def test_budget_stops_before_generation(self):
        self.client.request.side_effect=[{"inputTokenLimit":1000000,"outputTokenLimit":8192},{"totalTokens":100}]
        r=workflows.run_step6_batch(self.root,max_input_tokens=50,allow_api=True)
        self.assertEqual(r["generation_requests"],0);self.assertEqual(r["state"],"batch_input_budget_reached")
    def test_oversized_is_blocked_intact_not_budget_loop(self):
        self.client.request.side_effect=[{"inputTokenLimit":2000000,"outputTokenLimit":8192},{"totalTokens":1500000}]
        r=workflows.run_step6_batch(self.root,allow_api=True)
        self.assertEqual(r["blocked"],1);self.assertEqual(r["generation_requests"],0)
        record=json.loads((Path(r["folder"])/(self.hash+".json")).read_text())
        self.assertFalse(record["trace_was_trimmed"])
    def test_request_error_stops_and_is_not_retried(self):
        self.client.request.side_effect=[{"inputTokenLimit":1000000,"outputTokenLimit":8192},{"totalTokens":100},RuntimeError("Gemini HTTP 429; no retry was attempted")]
        r=workflows.run_step6_batch(self.root,allow_api=True)
        self.assertEqual(r["state"],"stopped_api_or_transport_error")
        self.assertEqual(workflows.run_step6_batch(self.root,allow_api=True)["generation_requests"],0)
    def test_heldout_blocked_while_development_unattempted(self):
        with self.assertRaises(RuntimeError):workflows.run_step6_batch(self.root,split="heldout",allow_api=True)
        self.client.request.assert_not_called()
    def test_token_preflight_failure_stops_without_generation(self):
        self.client.request.side_effect=[{"inputTokenLimit":1000000,"outputTokenLimit":8192},RuntimeError("Gemini HTTP 400; no retry was attempted")]
        r=workflows.run_step6_batch(self.root,allow_api=True)
        self.assertEqual(r["state"],"stopped_preflight_error");self.assertEqual(r["generation_requests"],0)

    def test_quiet_mode_keeps_per_trace_logs_out_of_notebook(self):
        import io, contextlib
        self.client.request.side_effect=[{"inputTokenLimit":1000000,"outputTokenLimit":8192},{"totalTokens":100},self.response]
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            result=workflows.run_step6_batch(self.root,allow_api=True,verbose=False)
        self.assertEqual(result["valid"],1)
        self.assertEqual(stream.getvalue(),"")
        record=json.loads((Path(result["folder"])/(self.hash+".json")).read_text())
        self.assertIn("runner_code_sha256",record)

    def test_post_batch_summary_uses_current_totals_and_new_error(self):
        import io, contextlib
        progress={"coverage":{"development":{"total":1214,"statuses":{"valid":76,"unattempted":1109,"invalid_response":23}},"heldout":{"total":323,"statuses":{"unattempted":323}}},"latest_record_update":"fresh timestamp","batch_lock_exists":False,"supervisor_lock_exists":False,"all_traces_accounted_for":False}
        result={"state":"stopped_api_or_transport_error","generation_requests":16,"valid":11,"invalid":4,"error":"Gemini HTTP 503; no retry was attempted"}
        stream=io.StringIO()
        with patch.object(workflows,"evaluation_progress",return_value=progress),contextlib.redirect_stdout(stream):
            returned=workflows.print_evaluation_summary(self.root,batch_result=result)
        output=stream.getvalue()
        self.assertIn("76 valid",output)
        self.assertIn("1109 unattempted",output)
        self.assertIn("Gemini HTTP 503",output)
        self.assertNotIn("paused_or_stopped",output)
        self.assertEqual(returned,progress)
