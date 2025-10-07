import enum
import logging
from io import TextIOBase
from typing import Dict, List, Optional

from simplini.core import (
    IniConfigBase,
    IniConfigOption,
    IniConfigSection,
    IniFlavour,
    SimpliniError,
    ValuePresentationStyle,
)

LOGGER = logging.getLogger(__name__)


class ValuesRenderingStyle(enum.Enum):
    PREFER_QUOTED = 0
    PREFER_UNQUOTED = 1
    PREFER_SOURCE = 2


class RenderingError(SimpliniError):
    pass


class RenderingContext:
    def __init__(
        self,
        config: IniConfigBase,
        flavour: IniFlavour,
        text_io: TextIOBase,
    ):
        self.config = config
        self.flavour = flavour
        self.text_io = text_io

    # convenience shortcuts
    @property
    def spacer(self) -> str:
        return self.flavour.new_line

    @property
    def comment_marker(self) -> str:
        return self.flavour.comment_markers[0]

    @property
    def new_line(self) -> str:
        return self.flavour.new_line

    @property
    def key_value_separator(self) -> str:
        return self.flavour.key_value_separators[0]

    @property
    def quote_character(self) -> str:
        return self.flavour.quote_character

    @property
    def escape_character(self) -> str:
        return self.flavour.escape_character

    # TODO: make sure NOT to replace ALL
    @property
    def escape_sequences(self) -> Dict[str, str]:
        # reverse the mapping
        return {v: k for k, v in self.flavour.escape_sequences.items()}


class IniConfigRenderer:
    def __init__(self):
        super().__init__()
        self.values_rendering_style: ValuesRenderingStyle = (
            ValuesRenderingStyle.PREFER_QUOTED
        )

    def write_spacer(
        self,
        ctx: RenderingContext,
    ):
        text_io = ctx.text_io
        if text_io.tell() != 0:
            text_io.write(ctx.spacer)

    def write_comments(
        self,
        ctx: RenderingContext,
        comments: Optional[List[str]] = None,
    ) -> None:
        text_io = ctx.text_io
        for comment_line in comments or []:
            if comment_line:
                text_io.write(f"{ctx.comment_marker} {comment_line}{ctx.new_line}")
            else:  # edge case for empty comment lines (avoid extra space)
                text_io.write(f"{ctx.comment_marker}{ctx.new_line}")

    def write_section(
        self,
        ctx: RenderingContext,
        section: IniConfigSection,
    ) -> None:
        text_io = ctx.text_io

        self.write_spacer(ctx)
        self.write_comments(ctx, section.comment)

        if section.name:
            text_io.write(f"[{section.name}]")

            if section.inline_comment:
                text_io.write(f"  {ctx.comment_marker} {section.inline_comment}")

            text_io.write(ctx.new_line)
        else:
            LOGGER.warning(
                "rendering inline comment for unnamed section, the semantic "
                "is not correct and it will be rendered as regular comment"
            )
            if section.inline_comment:
                text_io.write(f"{ctx.comment_marker} {section.inline_comment}")
                text_io.write(ctx.new_line)

        for option in section.options.values():
            self.write_option(ctx, option)

    def write_option(
        self,
        ctx: RenderingContext,
        option: IniConfigOption,
    ) -> None:
        text_io = ctx.text_io

        self.write_spacer(ctx)
        self.write_comments(ctx, option.comment)

        text_io.write(option.name)
        text_io.write(f" {ctx.key_value_separator} ")

        self.write_option_value(ctx, option)

        if option.inline_comment:
            text_io.write(f"  {ctx.comment_marker} {option.inline_comment}")

        text_io.write(ctx.new_line)

    def is_value_safe_to_be_unquoted(
        self,
        ctx: RenderingContext,
        s: str,
    ) -> bool:
        return (
            s == s.strip()
            and (
                not ctx.flavour.allow_inline_comments
                or not any(c in s for c in ctx.flavour.comment_markers)
            )
            and not s.startswith(ctx.quote_character)
            and not s.endswith(ctx.quote_character)
            and ctx.new_line not in s
        )

    def write_option_value(
        self,
        ctx: RenderingContext,
        option: IniConfigOption,
    ) -> None:
        value = option.value
        if self.values_rendering_style == ValuesRenderingStyle.PREFER_UNQUOTED:
            if self.is_value_safe_to_be_unquoted(ctx, value):
                self.write_unquoted_value(ctx, value)
            elif ctx.new_line in value:
                self.write_triple_quoted_value(ctx, value)
            else:
                self.write_quoted_value(ctx, value)
        elif (
            self.values_rendering_style == ValuesRenderingStyle.PREFER_SOURCE
            and option.style is not None
        ):
            if (
                option.style == ValuePresentationStyle.UNQUOTED
                and self.is_value_safe_to_be_unquoted(ctx, value)
            ):
                self.write_unquoted_value(ctx, value)
            elif option.style == ValuePresentationStyle.TRIPLE_QUOTED:
                self.write_triple_quoted_value(ctx, value)
            elif option.style == ValuePresentationStyle.QUOTED:
                self.write_quoted_value(ctx, value)
            else:
                # fallback for source unquoted unsafe value
                self.write_quoted_value(ctx, value)
        elif self.values_rendering_style == ValuesRenderingStyle.PREFER_QUOTED:
            if ctx.new_line in value:
                self.write_triple_quoted_value(ctx, value)
            else:
                self.write_quoted_value(ctx, value)

    def write_unquoted_value(
        self,
        ctx: RenderingContext,
        value: str,
    ) -> None:
        text_io = ctx.text_io
        assert self.is_value_safe_to_be_unquoted(ctx, value)
        text_io.write(value)

    def write_quoted_value(
        self,
        ctx: RenderingContext,
        value: str,
    ) -> None:
        text_io = ctx.text_io
        text_io.write(ctx.quote_character)
        for char in value:
            if char in ctx.escape_sequences:
                text_io.write(ctx.escape_character)
                text_io.write(ctx.escape_sequences[char])
            else:
                text_io.write(char)
        text_io.write(ctx.quote_character)

    def write_triple_quoted_value(
        self,
        ctx: RenderingContext,
        value: str,
    ) -> None:
        text_io = ctx.text_io
        text_io.write(ctx.quote_character * 3)
        # inside the triple quoted values we only need to escape the triple
        # quote itself, and escape character if it is used literally
        idx = 0
        while idx < len(value):
            if value[idx] == ctx.escape_character:
                text_io.write(ctx.escape_character * 2)
            elif value.startswith(ctx.quote_character * 3, idx):
                text_io.write(ctx.escape_character)
                text_io.write(ctx.quote_character * 3)
                idx += 2
            else:
                text_io.write(value[idx])
            idx += 1
        text_io.write(ctx.quote_character * 3)

    def render(
        self, text_io: TextIOBase, config: IniConfigBase, flavour: IniFlavour
    ) -> None:
        ctx = RenderingContext(
            config=config,
            flavour=flavour,
            text_io=text_io,
        )

        if config.unnamed_section.options or config.unnamed_section.comment:
            if not flavour.allow_unnamed_section:
                raise RenderingError("Unnamed section is not allowed")
            self.write_section(ctx, config.unnamed_section)

        for section in config.sections.values():
            self.write_section(ctx, section)

        if config.trailing_comment:
            self.write_spacer(ctx)
            self.write_comments(ctx, config.trailing_comment)
