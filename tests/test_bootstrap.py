from pathlib import Path
import sys
import unittest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.__main__ import main


class BootstrapLayoutTest(unittest.TestCase):
    def test_placeholder_entrypoint_is_importable_and_exits(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main()

        self.assertEqual(
            str(context.exception),
            "Application startup not implemented yet",
        )
