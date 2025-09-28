class IniConfigOption:
    def __init__(self, key: str, value: str):
        super().__init__()
        self.key = key
        self.value = value
        self.comment: list[str] | None = None
        self.inline_comment: str | None = None


class IniConfigSection:
    def __init__(self, name: str | None):
        super().__init__()
        self.name: str | None = name
        self.options: dict[str, IniConfigOption] = {}
        self.comment: list[str] | None = None

    def set(self, key: str, value: str) -> IniConfigOption:
        option = self.get(key) or IniConfigOption(key, value)
        self.options[key] = option
        return option

    def get(self, key: str) -> IniConfigOption | None:
        return self.options.get(key)

    def __getitem__(self, key: str) -> IniConfigOption:
        option = self.get(key)
        if option is None:
            raise KeyError(f"Option '{key}' not found in section '{self.name}'")
        return option

    @property
    def is_empty(self):
        return not self.comment and not self.options


class IniConfigBase:
    def __init__(self):
        super().__init__()
        self.unnamed_section = IniConfigSection(None)
        self.sections: dict[str, IniConfigSection] = {}
        self.trailing_comment: list[str] | None = None

    def get_section(self, section: str) -> IniConfigSection | None:
        return self.sections.get(section)

    def ensure_section(self, name: str) -> IniConfigSection:
        if name not in self.sections:
            self.sections[name] = IniConfigSection(name)
        return self.sections[name]
