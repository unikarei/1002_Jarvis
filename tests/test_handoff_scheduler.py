import unittest
from jarvis.handoff.scheduler import build_startup_task

class SchedulerTests(unittest.TestCase):
    def test_builds_limited_on_logon_task_without_executing_it(self):
        task = build_startup_task(python_executable="C:/Python/python.exe")
        self.assertEqual(task.command[:2], ("schtasks.exe", "/Create"))
        self.assertIn("/SC", task.command); self.assertIn("ONLOGON", task.command); self.assertIn("/RL", task.command); self.assertIn("LIMITED", task.command)
