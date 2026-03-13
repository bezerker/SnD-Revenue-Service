from pathlib import Path
import sys
import unittest
from unittest import mock

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.__main__ import main


class BootstrapLayoutTest(unittest.TestCase):
    def test_entrypoint_exits_with_config_error_when_runtime_config_is_missing(
        self,
    ) -> None:
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(SystemExit) as context:
                main()

        self.assertEqual(
            str(context.exception),
            "SND_REVENUE_CONFIG must point to the runtime TOML file",
        )
