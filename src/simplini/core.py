import enum
from typing import Dict, List, Optional


class ValuePresentationStyle(enum.Enum):
    UNQUOTED = 0
    QUOTED = 1
    TRIPLE_QUOTED = 2


class SimpliniError(Exception):
    pass


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

    def set(self, key: str, value: str) -> IniConfigOption:
        option = self.get(key) or IniConfigOption(key, value)
        self.options[key] = option
        return option

    def get(self, key: str) -> Optional[IniConfigOption]:
        return self.options.get(key)

    def __getitem__(self, key: str) -> IniConfigOption:
        option = self.get(key)
        if option is None:
            raise KeyError(f"Option '{key}' not found in section '{self.name}'")
        return option

    def __repr__(self) -> str:
        return f"IniConfigSection({self.name!r})"

    def as_dict(self) -> Dict:
        return {option.key: option.value for option in self.options.values()}


class IniConfigBase:
    def __init__(self):
        super().__init__()
        self.unnamed_section = IniConfigSection(None)
        self.sections: Dict[str, IniConfigSection] = {}
        self.trailing_comment: Optional[List[str]] = None

    def get_section(self, section: str) -> Optional[IniConfigSection]:
        return self.sections.get(section)

    def ensure_section(self, name: str) -> IniConfigSection:
        if name not in self.sections:
            self.sections[name] = IniConfigSection(name)
        return self.sections[name]

    def as_dict(self) -> Dict:
        result = {}

        if self.unnamed_section.options:
            result[""] = self.unnamed_section.as_dict()

        for section in self.sections.values():
            result[section.name] = section.as_dict()

        return result
