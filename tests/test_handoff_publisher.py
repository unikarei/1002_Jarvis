from datetime import UTC, datetime
import unittest
import yaml

from jarvis.handoff.publisher import ResultPublisher


class PublisherTests(unittest.TestCase):
    def test_publishes_only_new_correlated_result_envelope(self):
        class Writer:
            values = []
            def append(self, value): self.values.append(value)
        writer = Writer()
        ResultPublisher(writer, clock=lambda: datetime(2026, 8, 16, tzinfo=UTC)).publish_result(correlation_id="22222222-2222-4222-8222-222222222222", reply_to="11111111-1111-4111-8111-111111111111", summary="done", test_summary="passed")
        value = yaml.safe_load(writer.values[0].split("```yaml\n", 1)[1].split("```", 1)[0])
        self.assertEqual(value["sender"], "jarvis"); self.assertEqual(value["recipient"], "mitir")
        self.assertEqual(value["type"], "result_response"); self.assertEqual(value["payload"]["test_summary"], "passed")
