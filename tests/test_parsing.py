import logging
import os

from simplini import IniConfig, IniFlavour, ParsingError
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
            config.trailing_comment,
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

    def test_whitespaces_after_section_header_are_allowed(self):
        path = self.gen_temp_config("[section]   \nfoo=bar")

        config = IniConfig.load(path)

        self.assertIn("section", config.sections)
        self.assertIn("foo", config.sections["section"].options)
        self.assertEqual("bar", config.sections["section"]["foo"].value)

    def test_comment_after_section_header(self):
        path = self.gen_temp_config("[section] # allowed\nfoo=bar")

        config = IniConfig.load(path)

        self.assertEqual("allowed", config.sections["section"].inline_comment)

    def test_single_comment_with_whitespace_on_next_line(self):
        path = self.gen_temp_config("# comment\n ")

        config = IniConfig.load(path)

        self.assertEqual(["comment"], config.trailing_comment)

    def test_whitespace_before_comment(self):
        path = self.gen_temp_config(" # comment1\n # comment2\n")

        config = IniConfig.load(path)

        self.assertEqual(["comment1", "comment2"], config.trailing_comment)

    def test_single_key_value_with_whitespace_on_next_line(self):
        path = self.gen_temp_config("key = value\n ")

        config = IniConfig.load(path)

        self.assertEqual(
            {
                "": {
                    "key": "value",
                },
            },
            config.as_dict(),
        )


class InvalidConfigParsingCases(CaseBase):
    def test_not_closed_literal(self):
        path = self.gen_temp_config(
            'value = "this is invalid\n',
            # use Unix style new lines for all platforms, so that test
            # can report same positions
            newline="\n",
        )

        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 1, Column 25, Byte 25",
        ) as ctx:
            IniConfig.load(path)

        # check position context
        self.assertIsNotNone(ctx.exception)
        self.assertEqual(25, ctx.exception.position)
        self.assertIsNotNone(ctx.exception.position_context)
        self.assertEqual(1, ctx.exception.position_context.line_number)
        self.assertEqual(25, ctx.exception.position_context.column_number)

    def test_not_closed_literal_crlf(self):
        path = self.gen_temp_config(
            'value = "this is invalid\n',
            # force Windows style new lines (CRLF)
            newline="\r\n",
        )

        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 1, Column 26, Byte 26",
        ):
            IniConfig.load(path)

    def test_not_closed_literal_no_new_line(self):
        path = self.gen_temp_config('value = "this is invalid')

        self.assertRaisesRegex(
            ParsingError,
            "EOF encountered before closing quoted string",
            IniConfig.load,
            path,
        )

    def test_not_closed_section(self):
        config = "[this-is-not-valid-section\n"
        path = self.gen_temp_config(config)

        self.assertRaisesRegex(
            ParsingError, 'Expected "]", but encountered LF', IniConfig.load, path
        )

    def test_not_closed_section_no_new_line(self):
        config = "[this-is-not-valid-section"
        path = self.gen_temp_config(config)

        self.assertRaisesRegex(
            ParsingError, 'Expected "]", but encountered EOF', IniConfig.load, path
        )

    def test_invalid_escape_sequence(self):
        cases = [
            r'value = "foo\=bar"',
            r'value = "foo\xbar"',
            r'value = "foo\0bar"',
        ]

        for case in cases:
            path = self.gen_temp_config(case)

            self.assertRaisesRegex(
                ParsingError, "Unknown escape sequence", IniConfig.load, path
            )

    def test_not_closed_literal_on_second_line(self):
        path = self.gen_temp_config(
            'foo = bar\nvalue = "this is invalid\n',
            # use Unix style new lines for all platforms, so that test
            # can report same positions
            newline="\n",
        )
        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 2, Column 25, Byte 35",
        ):
            IniConfig.load(path)

    def test_not_closed_literal_on_second_line_crlf(self):
        path = self.gen_temp_config(
            'foo = bar\nvalue = "this is invalid\n',
            # force Windows style new lines (CRLF)
            newline="\r\n",
        )
        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 2, Column 26, Byte 37",
        ):
            IniConfig.load(path)

    def test_error_position_reporting_with_multibytes_characters(self):
        path = self.gen_temp_config(
            'foo = "хэлоу"\nvalue = "тест\n',
            newline="\n",
        )

        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 2, Column 14, Byte 37",
        ):
            IniConfig.load(path)

    def test_error_position_reporting_with_multibytes_characters_crlf(self):
        path = self.gen_temp_config(
            'foo = "хэлоу"\nvalue = "тест\n',
            newline="\r\n",
        )

        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 2, Column 15, Byte 39",
        ):
            IniConfig.load(path)

    def test_error_position_reporting_with_multibytes_characters_mid(self):
        path = self.gen_temp_config(
            'foo = "хэлоу"\nbar = "ворлд"\nvalue = "тест\nspam = eggs',
            newline="\n",
        )

        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 4, Column 1, Byte 56",
        ):
            IniConfig.load(path)

    def test_error_position_reporting_with_multibytes_characters_mid_crlf(self):
        path = self.gen_temp_config(
            'foo = "хэлоу"\nbar = "ворлд"\nvalue = "тест\nspam = eggs',
            newline="\r\n",
        )

        with self.assertRaisesRegex(
            ParsingError,
            "(?s)"  # dotall flag
            "New line encountered before closing quoted string"
            ".+"
            "Line 4, Column 1, Byte 59",
        ):
            IniConfig.load(path)

    def test_invalid_key_name(self):
        path = self.gen_temp_config('foo"key = bad')

        with self.assertRaisesRegex(
            ParsingError, 'Expected "=", but encountered """'
        ) as ctx:
            IniConfig.load(path)

        # verify full error message
        self.assertEqual(
            str(ctx.exception),
            """Expected "=", but encountered ""\"

  ...
> foo"key = bad
     ^
Line 1, Column 4, Byte 4
""",
        )

    def test_key_defined_on_same_line_with_section_is_not_allowed(self):
        path = self.gen_temp_config("[section] key = value")

        with self.assertRaisesRegex(
            ParsingError, "Expected end of line after section header"
        ):
            IniConfig.load(path)

    def test_not_closed_triple_quoted_literal(self):
        path = self.gen_temp_config('foo="""')

        with self.assertRaisesRegex(
            ParsingError, "EOF encountered before closing triple quoted string"
        ):
            IniConfig.load(path)

    def test_unnamed_section_when_not_allowed(self):
        path = self.gen_temp_config("foo = bar")
        with self.assertRaisesRegex(
            ParsingError,
            "Unnamed section is not allowed",
        ):
            flavour = IniFlavour()
            flavour.allow_unnamed_section = False
            IniConfig.load(path, flavour=flavour)
