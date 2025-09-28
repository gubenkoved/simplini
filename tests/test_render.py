import os

from simplini import IniConfig
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
