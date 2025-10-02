import enum
from io import TextIOBase
from typing import List, Optional

from simplini.core import (
    IniConfigBase,
    IniConfigOption,
    IniConfigSection,
    SimpliniError,
    ValuePresentationStyle,
)


class ValuesRenderingStyle(enum.Enum):
    PREFER_QUOTED = 0
    PREFER_UNQUOTED = 1
    PREFER_SOURCE = 2


class RenderingError(SimpliniError):
    pass


class IniConfigRenderer:
    def __init__(self):
        super().__init__()
        self.spacer = "\n"
        self.new_line = "\n"
        self.escape_character = "\\"
        self.escape_sequences = {
            "\\": "\\",
            '"': '"',
            "\n": "n",
        }
        # not all the escape sequences characters as they are NOT evaluated
        # as part of unquoted strings
        self.unsafe_unquoted_characters = ["#", '"']
        self.values_rendering_style: ValuesRenderingStyle = (
            ValuesRenderingStyle.PREFER_QUOTED
        )

    def write_spacer(self, text_io: TextIOBase):
        if text_io.tell() != 0:
            text_io.write(self.spacer)

    def write_comments(
        self,
        text_io: TextIOBase,
        comments: Optional[List[str]] = None,
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

        self.write_option_value(text_io, option)

        if option.inline_comment:
            text_io.write(f"  # {option.inline_comment}")

        text_io.write(self.new_line)

    def is_value_safe_to_be_unquoted(self, s: str) -> bool:
        return (
            s == s.strip()
            and not any(c in s for c in self.unsafe_unquoted_characters)
            and self.new_line not in s
        )

    def write_option_value(self, text_io: TextIOBase, option: IniConfigOption) -> None:
        value = option.value
        if self.values_rendering_style == ValuesRenderingStyle.PREFER_UNQUOTED:
            if self.is_value_safe_to_be_unquoted(value):
                self.write_unquoted_value(text_io, value)
            elif self.new_line in value:
                self.write_triple_quoted_value(text_io, value)
            else:
                self.write_quoted_value(text_io, value)
        elif (
            self.values_rendering_style == ValuesRenderingStyle.PREFER_SOURCE
            and option.style is not None
        ):
            if (
                option.style == ValuePresentationStyle.UNQUOTED
                and self.is_value_safe_to_be_unquoted(value)
            ):
                self.write_unquoted_value(text_io, value)
            elif option.style == ValuePresentationStyle.TRIPLE_QUOTED:
                self.write_triple_quoted_value(text_io, value)
            elif option.style == ValuePresentationStyle.QUOTED:
                self.write_quoted_value(text_io, value)
            else:
                # fallback for source unquoted unsafe value
                self.write_quoted_value(text_io, value)
        elif self.values_rendering_style == ValuesRenderingStyle.PREFER_QUOTED:
            if self.new_line in value:
                self.write_triple_quoted_value(text_io, value)
            else:
                self.write_quoted_value(text_io, value)

    def write_unquoted_value(self, text_io: TextIOBase, value: str) -> None:
        assert self.is_value_safe_to_be_unquoted(value)
        text_io.write(value)

    def write_quoted_value(self, text_io: TextIOBase, value: str) -> None:
        text_io.write('"')
        for char in value:
            if char in self.escape_sequences:
                text_io.write(self.escape_character)
                text_io.write(self.escape_sequences[char])
            else:
                text_io.write(char)
        text_io.write('"')

    # TODO: replace triple quotes inside the value, see TOML for reference
    def write_triple_quoted_value(self, text_io: TextIOBase, value: str) -> None:
        text_io.write('"""')
        text_io.write(value)
        text_io.write('"""')

    def render(self, text_io: TextIOBase, config: IniConfigBase) -> None:
        if config.unnamed_section.options or config.unnamed_section.comment:
            self.write_section(text_io, config.unnamed_section)

        for section in config.sections.values():
            self.write_section(text_io, section)

        if config.trailing_comment:
            self.write_spacer(text_io)
            self.write_comments(text_io, config.trailing_comment)
