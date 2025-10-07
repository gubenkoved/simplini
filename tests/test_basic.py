import logging
import os

from simplini import IniConfig
from tests.common import CaseBase

LOGGER = logging.getLogger(__name__)

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(CUR_DIR, "fixtures")


class BasicCases(CaseBase):
    def test_from_readme(self):
        path = self.get_temp_path()

        # create a new INI config
        config = IniConfig()

        # add values to the default section
        config.set("app_name", "My App")
        config.set("version", "1.0.0")

        # you can use section object to interact with section settings
        db_section = config.ensure_section("database")
        db_section.comment = ['Contains database settings']

        db_provider_opt = db_section.set("provider", "mysql")
        db_provider_opt.comment = [
            "Controls the DB provider to be used"
        ]

        # ... or set values directly via root config object
        config.set("version", "1.2.3", section_name="database")

        # save to file
        config.save(path)

        # load back from file
        loaded_config = IniConfig.load(path)

        app_name = loaded_config.get("app_name")
        version = loaded_config.get("version")

        db_section = loaded_config.get_section("database")

        self.assertIsNotNone(db_section)

        db_provider = db_section.get("provider")
        db_version = db_section.get("version")

        self.assertEqual("My App", app_name)
        self.assertEqual("1.0.0", version)
        self.assertEqual("mysql", db_provider)
        self.assertEqual("1.2.3", db_version)

        with open(path, "r") as file:
            actual_config = file.read()
            self.assertExpectedConfig(
                os.path.join(FIXTURES_DIR, "readme.ini"),
                actual_config,
            )

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
            self.assertEqual(value, config2.unnamed_section["value"])

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
            self.assertEqual("some_value", config2.unnamed_section[option_name])

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
        self.assertEqual("My App", loaded_config.unnamed_section["app_name"])
        self.assertEqual("1.0.0", loaded_config.unnamed_section["version"])

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

        self.assertEqual("bar", config2.unnamed_section["foo"])
        self.assertEqual("baz", config2.unnamed_section["bar"])

        foo_section = config2.sections["foo"]
        self.assertEqual("here", foo_section["val1"])
        self.assertEqual("here2", foo_section["val2"])
        self.assertEqual("has back\\slash", foo_section["val3"])
        self.assertEqual(["empty"], foo_section.get_option("val4").comment)
        self.assertEqual("", foo_section["val4"])
        self.assertEqual("multi\nline\nvalue", foo_section["val5"])

        bar_section = config2.sections["bar"]
        self.assertEqual("bar", bar_section["foo"])

    def test_config_as_dict(self):
        config = IniConfig()

        config.unnamed_section.set("foo", "bar")

        foo_sect = config.ensure_section("foo")
        foo_sect.set("val1", "here")
        foo_sect.set("val2", "here2")

        self.assertEqual(
            {
                "": {
                    "foo": "bar",
                },
                "foo": {
                    "val1": "here",
                    "val2": "here2",
                },
            },
            config.as_dict(),
        )

    def test_set_config_using_value(self):
        config = IniConfig()

        self.assertNotIn("core", config)

        section = config.ensure_section("core")

        self.assertIn("core", config)

        self.assertNotIn("foo", section)

        section.set("foo", "bar")
        section["foo"] = "bar2"

        self.assertIn("foo", section)

        config.set("spam", "foo")
        config.set("spam", "eggs", section_name="foo")

        self.assertEqual(
            {
                "": {
                    "spam": "foo",
                },
                "core": {
                    "foo": "bar2",
                },
                "foo": {
                    "spam": "eggs",
                },
            },
            config.as_dict(),
        )

        # drop sections and some options
        del config["foo"]
        del config.unnamed_section["spam"]

        self.assertEqual(
            {
                "core": {
                    "foo": "bar2",
                },
            },
            config.as_dict(),
        )
