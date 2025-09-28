from simplini.core import IniConfigBase, IniConfigOption, IniConfigSection
from simplini.parser import IniParser, ParsingError
from simplini.renderer import IniConfigRenderer

__all__ = ["IniConfig", "IniConfigSection", "IniConfigOption", "ParsingError"]


class IniConfig(IniConfigBase):
    def __init__(self) -> None:
        super().__init__()
        self.encoding = "utf-8"
        self.renderer: IniConfigRenderer = IniConfigRenderer()

    def save(self, path: str) -> None:
        with open(path, "w", encoding=self.encoding) as file:
            self.renderer.render(file, self)

    # TODO: allow changes in parser, also allow to bundle parser with IniConfig
    #  together (probably), the same as renderer
    @staticmethod
    def load(path: str, encoding: str = "utf-8") -> "IniConfig":
        with open(path, "r", encoding=encoding) as file:
            parser = IniParser(file)
            config = IniConfig()
            parser.parse_into(config)
            return config
