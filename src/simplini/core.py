import enum
from typing import Dict, List, Optional

UNNAMED_SECTION_NAME = ""


class ValuePresentationStyle(enum.Enum):
    UNQUOTED = 0
    QUOTED = 1
    TRIPLE_QUOTED = 2


class SimpliniError(Exception):
    pass


class IniFlavour:
    def __init__(self):
        self.allow_unquoted_values = True
        self.allow_unnamed_section = True
        # applies to key-value pairs only, as inline comments for sections
        # are not ambiguous anyway
        self.allow_inline_comments = True
        self.quote_character = '"'
        self.key_value_separators = ["="]
        self.comment_markers = ["#", ";"]
        self.escape_character = "\\"
        self.escape_sequences = {
            "n": "\n",
            "t": "\t",
            "\\": "\\",
            '"': '"',
            # when end of line is escaped,
            # the newline is ignored
            "\n": "",
        }
        self.new_line = "\n"
        self.whitespace_characters = [" ", "\t"]


class IniConfigOption:
    def __init__(self, key: str, value: str):
        super().__init__()
        self.key = key
        self.value = value
        self.comment: Optional[List[str]] = None
        self.inline_comment: Optional[str] = None
        self.style: Optional[ValuePresentationStyle] = None

    def __repr__(self) -> str:
        return f"IniConfigOption({self.key!r}, {self.value!r})"


class IniConfigSection:
    def __init__(self, name: Optional[str]):
        super().__init__()
        self.name: Optional[str] = name
        self.options: Dict[str, IniConfigOption] = {}
        self.comment: Optional[List[str]] = None
        self.inline_comment: Optional[str] = None

    def get_option(
        self,
        option_name: str,
    ) -> Optional[IniConfigOption]:
        return self.options.get(option_name)

    def set_option(
        self,
        option: IniConfigOption,
    ):
        self.options[option.key] = option

    def get_value(
        self,
        option_name: str,
    ) -> Optional[str]:
        option = self.options.get(option_name)
        if option is None:
            return None
        return option.value

    def set_value(
        self,
        option_name: str,
        value: str,
    ) -> IniConfigOption:
        if option_name in self.options:
            self.options[option_name].value = value
        else:
            self.options[option_name] = IniConfigOption(option_name, value)
        return self.options[option_name]

    def __getitem__(
        self,
        option_name: str,
    ) -> IniConfigOption:
        option = self.get_option(option_name)
        if option is None:
            raise KeyError(f'Option "{option_name}" not found in section "{self.name}"')
        return option

    def __contains__(
        self,
        option_name: str,
    ) -> bool:
        return option_name in self.options

    def __delitem__(
        self,
        option_name: str,
    ) -> None:
        if option_name not in self.options:
            raise KeyError(f'Option "{option_name}" not found in section "{self.name}"')
        del self.options[option_name]

    def __repr__(self) -> str:
        return f"IniConfigSection({self.name!r})"

    def as_dict(self) -> Dict:
        return {option.key: option.value for option in self.options.values()}


class IniConfigBase:
    def __init__(self):
        super().__init__()
        self.unnamed_section = IniConfigSection(UNNAMED_SECTION_NAME)
        self.sections: Dict[str, IniConfigSection] = {}
        self.trailing_comment: Optional[List[str]] = None

    def get_section(
        self,
        section_name: str,
    ) -> Optional[IniConfigSection]:
        return self.sections.get(section_name)

    def ensure_section(
        self,
        section_name: str,
    ) -> IniConfigSection:
        # unnamed section is always there
        if not section_name:
            return self.unnamed_section

        if section_name not in self.sections:
            self.sections[section_name] = IniConfigSection(section_name)

        return self.sections[section_name]

    def get_option(
        self,
        option_name: str,
        section_name: Optional[str] = None,
    ) -> Optional[IniConfigOption]:
        section = self.get_section(section_name)
        if section is None:
            return None
        return section.get_option(option_name)

    def set_option(
        self,
        option: IniConfigOption,
        section_name: Optional[str] = None,
    ) -> IniConfigOption:
        section = self.ensure_section(section_name)
        section.set_option(option)
        return option

    def get_value(
        self,
        option_name: str,
        section_name: Optional[str] = None,
    ) -> Optional[str]:
        if not section_name:
            section = self.unnamed_section
        else:
            section = self.get_section(section_name)
        if section is None:
            return None
        return section.get_value(option_name)

    def set_value(
        self,
        key: str,
        value: str,
        section_name: Optional[str] = None,
    ) -> IniConfigOption:
        section = self.ensure_section(section_name)
        section.set_value(key, value)
        return section[key]

    def __getitem__(self, section_name: str) -> IniConfigSection:
        if section_name not in self.sections:
            raise KeyError(f'Section "{section_name}" is not found')
        return self.sections[section_name]

    def __delitem__(self, section_name: str) -> None:
        del self.sections[section_name]

    def __contains__(self, section_name: str) -> bool:
        return section_name in self.sections

    def as_dict(self) -> Dict:
        result = {}

        if self.unnamed_section.options:
            result[UNNAMED_SECTION_NAME] = self.unnamed_section.as_dict()

        for section in self.sections.values():
            result[section.name] = section.as_dict()

        return result
