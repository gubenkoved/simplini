import os

from simplini import IniConfig
from simplini.renderer import RenderingError, ValuePresentationStyle
from tests.common import CaseBase

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(CUR_DIR, "fixtures")


class RenderCases(CaseBase):
    def test_simple_option(self):
        config = IniConfig()

        option = config.unnamed_section.set("val1", "value1")
        option.comment = [
            "line1",
            "line2",
        ]
        option.inline_comment = "inline comment"

        path = self.get_temp_path()
        config.save(path)

        self.assertExpectedConfig(
            os.path.join(FIXTURES_DIR, "render-simple.ini"), self.get_text(path)
        )

    def test_render_section(self):
        config = IniConfig()

        section = config.ensure_section("foo")
        section.comment = [
            "section comment line1",
            "section comment line2",
        ]

        option = section.set("val1", "value1")
        option.comment = [
            "option comment line1",
            "option comment line2",
        ]
        option.inline_comment = "inline comment"

        section.set("val2", "value2")

        path = self.get_temp_path()
        config.save(path)

        self.assertExpectedConfig(
            os.path.join(FIXTURES_DIR, "render-single-section.ini"),
            self.get_text(path),
        )

    def test_render_multiple_sections(self):
        config = IniConfig()

        section1 = config.ensure_section("foo")
        section1.set("foo", "foo-value")
        section1.set("bar", "bar-value")

        section2 = config.ensure_section("bar")
        section2.set("foo", "foo-value")
        section2.set("bar", "bar-value")

        path = self.get_temp_path()
        config.save(path)

        self.assertExpectedConfig(
            os.path.join(FIXTURES_DIR, "render-multiple-sections.ini"),
            self.get_text(path),
        )

    def test_rendering_error_when_unnamed_section_is_not_allowed(self):
        config = IniConfig()
        config.unnamed_section.set("foo", "value")

        config.flavour.allow_unnamed_section = False

        path = self.get_temp_path()

        with self.assertRaisesRegex(RenderingError, "Unnamed section is not allowed"):
            config.save(path)

    def test_triple_quotes_inside_triple_quoted_value(self):
        config = IniConfig()

        section = config.ensure_section("foo")

        option1 = section.set("value1", 'This\nis """ tricky...\nRight?')
        option2 = section.set("value2", "This is simple\nmultiline\nvalue")
        option3 = section.set(
            "value3", "There are\n  leading\nand trailing  \nspaces in this one"
        )

        for option in [option1, option2, option3]:
            option.style = ValuePresentationStyle.TRIPLE_QUOTED

        path = self.get_temp_path()

        config.save(path)

        self.assertExpectedConfig(
            os.path.join(FIXTURES_DIR, "render-triple-quoted.ini"),
            self.get_text(path),
        )

        # read-back and ensure the same content
        config2 = IniConfig.load(path)
        self.assertEqual(config.as_dict(), config2.as_dict())
