import logging
import os

from simplini import IniConfig
from tests.common import CaseBase

LOGGER = logging.getLogger(__name__)

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(CUR_DIR, "fixtures")


class BasicCases(CaseBase):
    def test_single_value(self):
        values = [
            "simple",
            "with_underscore",
            "with spaces",
            'with "quotes"',
            "with single 'quotes'",
            "with \\ backslash",
            "multi\nline\nvalue",
            " ",  # single space
            "\t",  # single tab
            "",
            '\'"""hello""" # world',
        ]

        for case_idx, value in enumerate(values):
            LOGGER.info(f'checking case #{case_idx}: "{value}"')
            path = self.get_temp_path()
            config = IniConfig()
            config.unnamed_section.set("value", value)
            config.save(path)

            # load it back
            config2 = IniConfig.load(path)
            self.assertEqual(value, config2.unnamed_section["value"].value)

    def test_option_names_cases(self):
        option_names = [
            "simple",
            "with_underscore",
            "with-dash",
            "with.dots",
            "with:mixed-._chars",
        ]

        for case_idx, option_name in enumerate(option_names):
            LOGGER.info(f'checking case #{case_idx}: "{option_name}"')
            path = self.get_temp_path()
            config = IniConfig()
            config.unnamed_section.set(option_name, "some_value")
            config.save(path)

            # load it back
            config2 = IniConfig.load(path)
            self.assertEqual("some_value", config2.unnamed_section[option_name].value)

    def test_unnamed_section_only_save_and_load(self):
        config = IniConfig()

        config.unnamed_section.set("app_name", "My App")
        config.unnamed_section.set("version", "1.0.0")

        config.unnamed_section.comment = [
            "Configuration for My App",
            "Created on 2025-09-28",
        ]

        path = self.get_temp_path()
        config.save(path)

        loaded_config = IniConfig.load(path)
        self.assertEqual("My App", loaded_config.unnamed_section["app_name"].value)
        self.assertEqual("1.0.0", loaded_config.unnamed_section["version"].value)

    def test_with_sections_save_and_load(self):
        config = IniConfig()

        config.unnamed_section.comment = [
            "this is default section comment",
            "that spans multiple lines",
        ]

        config.unnamed_section.set("foo", "bar")
        config.unnamed_section.set("bar", "baz")

        foo_sect = config.ensure_section("foo")
        foo_sect.comment = ["this is section comment", "that has multiple lines"]
        foo_sect.set("val1", "here")
        opt = foo_sect.set("val2", "here2")
        opt.comment = [
            "Here is option",
            "comment as well",
        ]

        foo_sect.set("val3", "has back\\slash")
        val4_opt = foo_sect.set("val4", "")
        val4_opt.comment = ["empty"]

        foo_sect.set("val5", "multi\nline\nvalue")

        bar_sect = config.ensure_section("bar")
        bar_sect.set("foo", "bar")

        path = self.get_temp_path()
        config.save(path)

        config2 = IniConfig.load(path)

        self.assertEqual("bar", config2.unnamed_section["foo"].value)
        self.assertEqual("baz", config2.unnamed_section["bar"].value)

        foo_section = config2.sections["foo"]
        self.assertEqual("here", foo_section["val1"].value)
        self.assertEqual("here2", foo_section["val2"].value)
        self.assertEqual("has back\\slash", foo_section["val3"].value)
        self.assertEqual(["empty"], foo_section["val4"].comment)
        self.assertEqual("", foo_section["val4"].value)
        self.assertEqual("multi\nline\nvalue", foo_section["val5"].value)

        bar_section = config2.sections["bar"]
        self.assertEqual("bar", bar_section["foo"].value)
