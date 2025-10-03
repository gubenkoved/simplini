from typing import Optional

from simplini.core import IniConfigBase, IniConfigOption, IniConfigSection, IniFlavour
from simplini.parser import IniParser, ParsingError
from simplini.renderer import IniConfigRenderer

__all__ = [
    "IniFlavour",
    "IniConfig",
    "IniConfigSection",
    "IniConfigOption",
    "ParsingError",
]


class IniConfig(IniConfigBase):
    def __init__(self) -> None:
        super().__init__()
        self.encoding = "utf-8"
        self.flavour = IniFlavour()
        self.renderer: IniConfigRenderer = IniConfigRenderer()

    def save(self, path: str) -> None:
        with open(path, "w", encoding=self.encoding) as file:
            self.renderer.render(file, self, self.flavour)

    @staticmethod
    def load(
        path: str,
        encoding: str = "utf-8",
        parser: Optional[IniParser] = None,
        flavour: Optional[IniFlavour] = None,
    ) -> "IniConfig":
        parser = parser or IniParser()

        # note that by default text reader will translate new lines into
        # LF-style even on Windows with CRLF new lines
        with open(path, "r", encoding=encoding) as file:
            config = IniConfig()
            config.flavour = flavour or IniFlavour()
            parser.parse(file, config, config.flavour)
            return config
