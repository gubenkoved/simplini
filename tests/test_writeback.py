import json
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
        source_path: str,
        writeback_path: str,
        configure_fn: Optional[Callable[[IniConfig], None]] = None,
    ):
        source_path = os.path.join(FIXTURES_DIR, source_path)
        writeback_path = os.path.join(FIXTURES_DIR, writeback_path)

        config = IniConfig.load(source_path)

        if configure_fn:
            configure_fn(config)

        temp_path = self.get_temp_path()

        config_data = config.as_dict()

        json_representation = json.dumps(config_data, indent=4).splitlines()

        if not config.trailing_comment:
            config.trailing_comment = []
        else:
            config.trailing_comment.append("")

        config.trailing_comment.append(
            "Writeback test-only automatically added JSON representation:"
        )
        config.trailing_comment.extend(json_representation)

        config.save(temp_path)

        with open(temp_path, "r") as file:
            actual_config = file.read()

        self.assertExpectedConfig(
            writeback_path,
            actual_config,
        )

        # read the config back and make sure data is still interpreted the same way
        loaded_back = IniConfig.load(
            path=writeback_path,
            flavour=config.flavour,
        )
        self.assertEqual(
            config_data,
            loaded_back.as_dict(),
        )

    def test_sample(self):
        self.generic_writeback_test(
            "sample.ini",
            "sample-writeback.ini",
        )

    def test_sample_prefer_unquoted(self):
        def configure(config: IniConfig):
            config.renderer.values_rendering_style = (
                ValuesRenderingStyle.PREFER_UNQUOTED
            )

        self.generic_writeback_test(
            "sample.ini",
            "sample-writeback-prefer-unquoted.ini",
            configure,
        )

    def test_sample_change_flavour(self):
        def configure(config: IniConfig):
            config.flavour.key_value_separators = [":"]
            config.flavour.comment_markers = [";"]
            config.flavour.quote_character = "'"
            config.flavour.escape_sequences["'"] = "'"

            # configure rendering style as well
            config.renderer.values_rendering_style = ValuesRenderingStyle.PREFER_SOURCE

        self.generic_writeback_test(
            "sample.ini",
            "sample-writeback-changed-flavour.ini",
            configure,
        )

    def test_sample_prefer_source(self):
        def configure(config: IniConfig):
            config.renderer.values_rendering_style = ValuesRenderingStyle.PREFER_SOURCE

        self.generic_writeback_test(
            "sample.ini",
            "sample-writeback-prefer-source.ini",
            configure,
        )

    def test_unquoted_value(self):
        self.generic_writeback_test(
            "unquoted-value.ini",
            "unquoted-value-writeback.ini",
        )

    def test_comments_with_new_lines(self):
        self.generic_writeback_test(
            "comments-with-new-lines.ini",
            "comments-with-new-lines-writeback.ini",
        )

    def test_comments_at_various_places(self):
        self.generic_writeback_test(
            "comments-various-places.ini",
            "comments-various-places-writeback.ini",
        )

    def test_trailing_comment_unnamed_section(self):
        self.generic_writeback_test(
            "trailing-comment-default-section.ini",
            "trailing-comment-default-section-writeback.ini",
        )

    def test_comments_compaction(self):
        self.generic_writeback_test(
            "comments-compaction.ini",
            "comments-compaction-writeback.ini",
        )

    def test_comment_with_empty_comment_lines_preserved(self):
        self.generic_writeback_test(
            "comments-with-empty-comment-lines.ini",
            "comments-with-empty-comment-lines-writeback.ini",
        )

    def test_escape_sequences(self):
        self.generic_writeback_test(
            "escape-sequences.ini",
            "escape-sequences-writeback.ini",
        )

    def test_empty_sections(self):
        self.generic_writeback_test(
            "empty-sections.ini",
            "empty-sections-writeback.ini",
        )

    def test_named_sections_only(self):
        self.generic_writeback_test(
            "named-sections-only.ini",
            "named-sections-only-writeback.ini",
        )

    def test_option_names(self):
        self.generic_writeback_test(
            "option-names.ini",
            "option-names-writeback.ini",
        )
