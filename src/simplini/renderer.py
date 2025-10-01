from io import TextIOBase
from typing import List, Optional

from simplini.core import IniConfigBase, IniConfigOption, IniConfigSection


class IniConfigRenderer:
    def __init__(self):
        super().__init__()
        self.spacer = "\n"
        self.escaped_characters = ["\\", '"']
        self.escape_character = "\\"

    def write_spacer(self, text_io: TextIOBase):
        if text_io.tell() != 0:
            text_io.write(self.spacer)

    def write_comments(
        self, text_io: TextIOBase, comments: Optional[List[str]] = None
    ) -> None:
        for comment_line in comments or []:
            if comment_line:
                text_io.write(f"# {comment_line}\n")
            else:  # edge case for empty comment lines (avoid extra space)
                text_io.write("#\n")

    def write_section(self, text_io: TextIOBase, section: IniConfigSection) -> None:
        self.write_spacer(text_io)

        self.write_comments(text_io, section.comment)

        if section.name:
            text_io.write(f"[{section.name}]\n")

        for option in section.options.values():
            self.write_option(text_io, option)

    def write_option(self, text_io: TextIOBase, option: IniConfigOption) -> None:
        self.write_spacer(text_io)
        self.write_comments(text_io, option.comment)

        text_io.write(option.key)
        text_io.write(" = ")

        if "\n" in option.value:
            self.write_multiline_value(text_io, option.value)
        else:
            self.write_single_line_value(text_io, option.value)

        if option.inline_comment:
            text_io.write(f"  # {option.inline_comment}")

        text_io.write("\n")

    def write_single_line_value(self, text_io: TextIOBase, value: str) -> None:
        text_io.write('"')
        for char in value:
            if char in self.escaped_characters:
                text_io.write(self.escape_character)
                text_io.write(char)
            else:
                text_io.write(char)
        text_io.write('"')

    # TODO: replace triple quotes inside the value, see TOML for reference
    def write_multiline_value(self, text_io: TextIOBase, value: str) -> None:
        text_io.write('"""')
        text_io.write(value)
        text_io.write('"""')

    def render(self, text_io: TextIOBase, config: IniConfigBase) -> None:
        if not config.unnamed_section.is_empty:
            self.write_section(text_io, config.unnamed_section)

        for section in config.sections.values():
            self.write_section(text_io, section)

        if config.trailing_comment:
            self.write_spacer(text_io)
            self.write_comments(text_io, config.trailing_comment)
