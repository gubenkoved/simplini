import logging
import os

from simplini import IniConfig, ParsingError
from tests.common import CaseBase

LOGGER = logging.getLogger(__name__)

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(CUR_DIR, "fixtures")


class ParsingTestCases(CaseBase):
    def test_load_sample_config(self):
        fixture_path = os.path.join(FIXTURES_DIR, "sample.ini")

        config = IniConfig.load(fixture_path)

        unnamed_section = config.unnamed_section

        self.assertEqual("value", unnamed_section["value_1"].value)
        self.assertEqual("value with spaces", unnamed_section["value_2"].value)
        self.assertEqual('value with "quotes"', unnamed_section["value_3"].value)
        self.assertEqual("value with 'single quotes'", unnamed_section["value_4"].value)
        self.assertEqual("multiline\nvalue", unnamed_section["value_5"].value)

        # check comments
        self.assertEqual(["comment for value1"], unnamed_section["value_1"].comment)
        self.assertEqual(
            "inline comment for value1",
            unnamed_section["value_1"].inline_comment,
        )
        self.assertEqual(["comment for value2"], unnamed_section["value_2"].comment)
        self.assertEqual(["comment for value3"], unnamed_section["value_3"].comment)
        self.assertEqual([], unnamed_section["value_4"].comment)
        self.assertEqual(["comment for value5"], unnamed_section["value_5"].comment)

        self.assertEqual(["custom"], list(config.sections))

        custom_section = config.sections["custom"]

        self.assertEqual(
            [
                "section comment",
                "goes here",
            ],
            custom_section.comment,
        )

        self.assertEqual("", custom_section["value_1"].value)
        self.assertEqual("", custom_section["value_2"].value)
        self.assertEqual("", custom_section["value_3"].value)
        self.assertEqual("hello", custom_section["value_4"].value)
        self.assertEqual("world", custom_section["value_5"].value)

    def test_unquoted_values(self):
        fixture_path = os.path.join(FIXTURES_DIR, "unquoted-value.ini")

        config = IniConfig.load(fixture_path)

        self.assertEqual("sample", config.unnamed_section["value1"].value)
        self.assertEqual(
            "sample with leading and trailing spaces",
            config.unnamed_section["value2"].value,
        )
        self.assertEqual("", config.unnamed_section["value3"].value)

        self.assertEqual("value", config.unnamed_section["value4"].value)
        self.assertEqual(
            "inline comment", config.unnamed_section["value4"].inline_comment
        )

    def test_comment_only_file(self):
        fixture_path = os.path.join(FIXTURES_DIR, "comment-only.ini")

        config = IniConfig.load(fixture_path)

        self.assertEqual(0, len(config.unnamed_section.options))
        self.assertEqual(0, len(config.sections))

        self.assertEqual(
            ["this is just a comment", "and nothing else"],
            config.unnamed_section.comment,
        )

    def test_new_lines_inside_comments(self):
        fixture_path = os.path.join(FIXTURES_DIR, "comments-with-new-lines.ini")

        config = IniConfig.load(fixture_path)

        self.assertEqual(
            [
                "value comment",
                "with new lines in between",
                "and even more lines in between",
            ],
            config.unnamed_section["value"].comment,
        )

        self.assertEqual(
            [
                "section comment",
                "can also have new lines in between",
            ],
            config.sections["foo"].comment,
        )

    def test_multiline_values(self):
        fixture_path = os.path.join(FIXTURES_DIR, "multiline-values.ini")

        config = IniConfig.load(fixture_path)

        foo_section = config.sections["foo"]
        self.assertEqual(
            "this is\na multiline\nvalue",
            foo_section["value"].value,
        )


class InvalidConfigParsingCases(CaseBase):
    def test_not_closed_literal(self):
        fixture_path = os.path.join(FIXTURES_DIR, "invalid-not-closed-literal.ini")

        self.assertRaises(
            ParsingError,
            lambda: IniConfig.load(fixture_path),
        )

    def test_not_closed_section(self):
        fixture_path = os.path.join(FIXTURES_DIR, "invalid-not-closed-section.ini")

        self.assertRaises(
            ParsingError,
            lambda: IniConfig.load(fixture_path),
        )

    def test_invalid_escape_sequence(self):
        cases = [
            r'value = "foo\=bar"',
            r'value = "foo\xbar"',
            r'value = "foo\0bar"',
        ]

        for case in cases:
            path = self.gen_temp_config(case)

            # TODO: enhance reporting parsing errors so that we can
            #  report back better error messages instead of falling back
            #  to very generic ones
            #
            # self.assertRaisesRegex(
            #     ParsingError,
            #     "Invalid escape sequence",
            #     lambda: IniConfig.load(path)
            # )

            self.assertRaises(ParsingError, IniConfig.load, path)
