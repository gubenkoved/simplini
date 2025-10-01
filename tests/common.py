import logging
import os
import tempfile
import unittest
from typing import Optional

LOGGER = logging.getLogger(__name__)


class CaseBase(unittest.TestCase):
    def get_temp_path(self) -> str:
        with tempfile.NamedTemporaryFile(delete=False, prefix="simplini-") as tmp:
            LOGGER.info(f"Using temp file: {tmp.name}")
            if os.environ.get("KEEP_TEMP_FILES") not in ("1", "true", "yes", "y"):
                self.addCleanup(os.unlink, tmp.name)
            return tmp.name

    def gen_temp_config(
        self,
        content: str,
        newline: Optional[str] = None,
        encoding: Optional[str] = "utf-8",
    ) -> str:
        path = self.get_temp_path()
        with open(path, "w", newline=newline, encoding=encoding) as f:
            f.write(content)
        return path

    def get_text(self, path: str, encoding="utf-8") -> str:
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    def assertExpectedConfig(self, expected_config_path: str, actual_config: str):
        if os.environ.get("UPDATE_EXPECTED_CONFIGS") in ("y", "1", "yes"):
            LOGGER.warning("updating expected config at %s", expected_config_path)
            with open(expected_config_path, "w") as f:
                f.write(actual_config)

        with open(expected_config_path, "r") as f:
            expected_config = f.read()

        self.assertEqual(expected_config, actual_config)
