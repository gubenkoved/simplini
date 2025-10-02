import logging
import os
from typing import Callable, Optional

from simplini import IniConfig
from simplini.renderer import ValuesRenderingStyle
from tests.common import CaseBase

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(CUR_DIR, "fixtures")

LOGGER = logging.getLogger(__name__)


class WriteBackCases(CaseBase):
    def generic_writeback_test(
        self,
        path: str,
        writeback_path: str,
        configure_fn: Optional[Callable[[IniConfig], None]] = None,
    ):
        config = IniConfig.load(path)

        if configure_fn:
            configure_fn(config)

        temp_path = self.get_temp_path()
        config.save(temp_path)

        with open(temp_path, "r") as file:
            actual_config = file.read()

        self.assertExpectedConfig(
            writeback_path,
            actual_config,
        )

    def test_sample(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "sample.ini"),
            os.path.join(FIXTURES_DIR, "sample-writeback.ini"),
        )

    def test_sample_prefer_unquoted(self):
        def configure(config: IniConfig):
            config.renderer.values_rendering_style = (
                ValuesRenderingStyle.PREFER_UNQUOTED
            )

        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "sample.ini"),
            os.path.join(FIXTURES_DIR, "sample-writeback-prefer-unquoted.ini"),
            configure,
        )

    def test_sample_prefer_source(self):
        def configure(config: IniConfig):
            config.renderer.values_rendering_style = ValuesRenderingStyle.PREFER_SOURCE

        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "sample.ini"),
            os.path.join(FIXTURES_DIR, "sample-writeback-prefer-source.ini"),
            configure,
        )

    def test_unquoted_value(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "unquoted-value.ini"),
            os.path.join(FIXTURES_DIR, "unquoted-value-writeback.ini"),
        )

    def test_comments_with_new_lines(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "comments-with-new-lines.ini"),
            os.path.join(FIXTURES_DIR, "comments-with-new-lines-writeback.ini"),
        )

    def test_comments_at_various_places(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "comments-various-places.ini"),
            os.path.join(FIXTURES_DIR, "comments-various-places-writeback.ini"),
        )

    def test_trailing_comment_unnamed_section(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "trailing-comment-default-section.ini"),
            os.path.join(
                FIXTURES_DIR, "trailing-comment-default-section-writeback.ini"
            ),
        )

    def test_comments_compaction(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "comments-compaction.ini"),
            os.path.join(FIXTURES_DIR, "comments-compaction-writeback.ini"),
        )

    def test_comment_with_empty_comment_lines_preserved(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "comments-with-empty-comment-lines.ini"),
            os.path.join(
                FIXTURES_DIR, "comments-with-empty-comment-lines-writeback.ini"
            ),
        )

    def test_escape_sequences(self):
        self.generic_writeback_test(
            os.path.join(FIXTURES_DIR, "escape-sequences.ini"),
            os.path.join(FIXTURES_DIR, "escape-sequences-writeback.ini"),
        )
