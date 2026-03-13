from pathlib import Path
import unittest


class BootstrapLayoutTest(unittest.TestCase):
    def test_project_uses_src_layout(self) -> None:
        self.assertTrue(Path("src/snd_revenue_service/__main__.py").exists())
