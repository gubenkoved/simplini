import functools
import logging
from io import TextIOBase
from typing import Callable, Dict, List, Optional, Tuple, TypeVar, Union

from simplini.core import (
    IniConfigBase,
    IniConfigOption,
    IniConfigSection,
    SimpliniError,
    ValuePresentationStyle,
)

T = TypeVar("T")


LOGGER = logging.getLogger(__name__)


class PositionContext:
    def __init__(
        self,
        line: str,
        line_number: int,
        column_number: int,
        lines_before: Optional[List[str]] = None,
    ):
        self.line = line
        # 1-based line number of the line
        self.line_number = line_number
        # 1-based position in the current line
        self.column_number = column_number
        # zero or multiple lines before the current line
        self.lines_before = lines_before


class ParsingError(SimpliniError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: str = message
        self.position: Optional[int] = None
        self.position_context: Optional[PositionContext] = None

    def extend_message(self, message: str) -> None:
        self.message += message
        self.args = (self.args[0] + message,) + self.args[1:]


class RecursiveDescentParserBase:
    def __init__(self, text_io: TextIOBase):
        self.text_io: TextIOBase = text_io
        self.deepest_error: Optional[ParsingError] = None

    def parsing_error(self, message: str) -> ParsingError:
        position = self.text_io.tell()

        error = ParsingError(message)
        error.position = position

        # update deepest error
        if self.deepest_error is None or position > self.deepest_error.position:
            self.deepest_error = error

        return error

    def expect(self, expected: str) -> str:
        char = self.text_io.read(1)

        if char != expected:
            if char == "\n":
                actual = "LF"
            elif char == "\r":
                actual = "CR"
            elif char == "":
                actual = "EOF"
            else:
                actual = f'"{char}"'

            raise self.parsing_error(f'Expected "{expected}", but encountered {actual}')

        return char

    def expect_eof(self) -> None:
        char = self.text_io.read(1)

        if char != "":
            raise self.parsing_error(f'Expected EOF, but encountered "{char}"')

        return None

    def accept(
        self, value_or_predicate: Union[Callable[[str], bool], str]
    ) -> Tuple[bool, Optional[str]]:
        char = self.text_io.read(1)

        # reached EOF
        if char == "":
            return False, None

        if not callable(value_or_predicate):

            def predicate(c: str) -> bool:
                return c == value_or_predicate
        else:
            predicate = value_or_predicate
            assert callable(predicate)

        if not predicate(char):
            self.text_io.seek(self.text_io.tell() - 1)
            return False, None

        return True, char

    def accept_multiple(
        self,
        value_or_predicate: Union[Callable[[str], bool], str],
    ) -> Tuple[bool, str]:
        chars = ""
        accepted, char = self.accept(value_or_predicate)

        if not accepted:
            return False, chars

        while accepted:
            assert char is not None
            chars += char
            accepted, char = self.accept(value_or_predicate)

        return True, chars

    def multiple(self, parse_fn: Callable[[], T]) -> List[T]:
        results = []

        while True:
            ok, result = self.optional(parse_fn)

            if not ok:
                break

            assert result is not None
            results.append(result)

        return results

    def optional(self, parse_fn: Callable[[], T]) -> Tuple[bool, Optional[T]]:
        position = self.text_io.tell()

        try:
            result = parse_fn()
            return True, result
        except ParsingError:
            self.text_io.seek(position)
            return False, None

    def choice(self, parse_fns: List[Callable[[], T]]) -> Tuple[int, T]:
        last_error = None
        position = self.text_io.tell()

        for parser_idx, parse_fn in enumerate(parse_fns):
            try:
                result = parse_fn()
                return parser_idx, result
            except ParsingError as e:
                last_error = e
                self.text_io.seek(position)

        assert last_error is not None
        raise last_error

    def peek(self, length: int) -> T:
        position = self.text_io.tell()
        peeked = self.text_io.read(length)
        self.text_io.seek(position)
        return peeked

    def hinted_choice(
        self, hinted_parse_fns: List[Tuple[Optional[str], Callable[[], T]]]
    ) -> Tuple[int, T]:
        position = self.text_io.tell()
        last_error = None

        for parser_idx, (hint, parse_fn) in enumerate(hinted_parse_fns):
            if hint:
                peeked = self.peek(len(hint))

                # hint matched, so we know this branch is what we need
                if hint == peeked:
                    return parser_idx, parse_fn()
            else:  # empty hint, attempt the branch and go to next if not successful
                try:
                    return parser_idx, parse_fn()
                except ParsingError as e:
                    self.text_io.seek(position)
                    last_error = e

        assert last_error is not None
        raise last_error


# TODO: extract grammatically important parts into a separate object like
#  Flavour that will be shared (or used) across parser and renderer to provide
#  consistent behaviour between parsing and rendering
class IniParserImpl(RecursiveDescentParserBase):
    def __init__(
        self,
        text_io: TextIOBase,
        allow_unquoted_values: bool,
        key_value_separator: str,
        comment_separator: str,
        escape_character: str,
        quote_character: str,
        escape_sequences: Dict[str, str],
        new_line: str,
    ):
        super().__init__(text_io)
        self.allow_unquoted_values = allow_unquoted_values
        self.key_value_separator = key_value_separator
        self.comment_separator = comment_separator
        self.escape_character = escape_character
        self.quote_character = quote_character
        self.escape_sequences = escape_sequences
        self.new_line = new_line

    def resolve_escape_sequence(self, sequence: str) -> str:
        if sequence not in self.escape_sequences:
            raise self.parsing_error(f"Unknown escape sequence: {sequence}")
        return self.escape_sequences[sequence]

    def parse_quoted_string(self) -> str:
        self.parse_whitespaces()

        self.expect(self.quote_character)

        value = ""

        while True:
            char = self.text_io.read(1)

            if char == self.escape_character:
                next_char = self.text_io.read(1)
                value += self.resolve_escape_sequence(char + next_char)
            elif char == self.new_line:
                raise self.parsing_error(
                    "New line encountered before closing quoted string"
                )
            elif char == "":
                raise self.parsing_error("EOF encountered before closing quoted string")
            else:  # normal character
                if char == self.quote_character:
                    break
                value += char

        # trailing whitespaces
        self.parse_whitespaces()

        return value

    def parse_triple_quoted_string(self) -> str:
        self.parse_whitespaces()

        self.expect(self.quote_character)
        self.expect(self.quote_character)
        self.expect(self.quote_character)

        value = ""

        while True:
            char = self.text_io.read(1)

            if char == self.escape_character:
                next_char = self.text_io.read(1)
                value += self.resolve_escape_sequence(char + next_char)
            else:  # normal character:
                if char == self.quote_character:
                    # check if it's the end of the triple-quoted string
                    next_char = self.text_io.read(1)
                    if next_char == self.quote_character:
                        next_next_char = self.text_io.read(1)
                        if next_next_char == self.quote_character:
                            break
                        else:
                            value += char + next_char + next_next_char
                    else:
                        value += char + next_char
                else:
                    value += char

        # trailing whitespaces
        self.parse_whitespaces()

        return value

    def parse_unquoted_string(self) -> str:
        self.parse_whitespaces()

        _, value = self.accept_multiple(
            lambda c: c not in (self.new_line, self.comment_separator),
            # even if nothing is accepted we consider the value to be empty
        )

        assert value is not None

        # strip trailing spaces
        value = value.rstrip()

        if self.quote_character in value:
            raise self.parsing_error(
                "Quote character inside non-quoted strings is forbidden as ambiguous"
            )

        # trailing whitespaces
        self.parse_whitespaces()

        return value

    def is_option_name_char(self, c: str) -> bool:
        # here is what TOML allows: A-Za-z0-9_-
        # see https://toml.io/en/v1.0.0
        # we will allow a bit more for now
        return c.isalnum() or c in ("_", "-", ".", ":")

    def parse_option_name(self) -> str:
        _, option_name = self.accept_multiple(
            self.is_option_name_char,
        )

        if not option_name:
            raise self.parsing_error("Expected option name to be non-empty string")

        return option_name

    def parse_option_value(self) -> Tuple[str, ValuePresentationStyle]:
        if self.allow_unquoted_values:
            parser_idx, value = self.hinted_choice(
                [
                    (self.quote_character * 3, self.parse_triple_quoted_string),
                    (self.quote_character, self.parse_quoted_string),
                    (None, self.parse_unquoted_string),
                ]
            )

            if parser_idx == 0:
                return value, ValuePresentationStyle.TRIPLE_QUOTED
            elif parser_idx == 1:
                return value, ValuePresentationStyle.QUOTED
            elif parser_idx == 2:
                return value, ValuePresentationStyle.UNQUOTED
            else:
                raise NotImplementedError(parser_idx)
        else:
            parser_idx, value = self.hinted_choice(
                [
                    (self.quote_character * 3, self.parse_triple_quoted_string),
                    (
                        self.quote_character,
                        self.parse_quoted_string,
                    ),
                ]
            )

            if parser_idx == 0:
                return value, ValuePresentationStyle.TRIPLE_QUOTED
            elif parser_idx == 1:
                return value, ValuePresentationStyle.QUOTED
            else:
                raise NotImplementedError(parser_idx)

    def parse_option(self) -> IniConfigOption:
        comments = self.parse_comments()
        self.parse_whitespaces()
        option_name = self.parse_option_name()
        self.parse_whitespaces()
        self.expect(self.key_value_separator)
        self.parse_whitespaces()

        option_value, option_value_style = self.parse_option_value()

        _, inline_comment = self.optional(self.parse_comment_line)
        self.multiple(self.parse_empty_line)

        option = IniConfigOption(option_name, option_value)
        option.comment = comments
        option.inline_comment = inline_comment
        option.style = option_value_style
        return option

    def is_whitespace(self, char: str) -> bool:
        return char in (" ", "\t")

    def parse_whitespaces(self) -> str:
        return self.accept_multiple(self.is_whitespace)[1]

    def parse_section_body(self, section: IniConfigSection) -> None:
        options = self.multiple(self.parse_option)

        for option in options:
            assert option is not None

            if option.key in section.options:
                raise self.parsing_error(
                    f'Option "{option.key}" was present multiple times'
                )

            section.options[option.key] = option

    def parse_comment_line(self) -> str:
        self.accept_multiple(self.is_whitespace)
        self.expect(self.comment_separator)

        _, comment = self.accept_multiple(
            lambda c: c != "\n",
        )

        # accept new line if present as well
        self.accept("\n")

        # strip leading/trailing spaces
        return comment.strip()

    def parse_empty_line(self) -> str:
        self.accept_multiple(self.is_whitespace)
        self.expect(self.new_line)
        return ""

    def parse_comments(self) -> List[str]:
        def parse_comment_or_empty_line() -> Tuple[int, str]:
            parser_idx, parsed_value = self.choice(
                [
                    self.parse_comment_line,
                    self.parse_empty_line,
                ]
            )
            return parser_idx, parsed_value

        parsed = self.multiple(parse_comment_or_empty_line)

        # drop empty lines
        comment_lines = [line for idx, line in parsed if idx == 0]

        # strip the comments
        return [comment.strip() for comment in comment_lines]

    def parse_section(self) -> IniConfigSection:
        comments = self.parse_comments()

        # parse section name
        self.expect("[")

        _, section_name = self.accept_multiple(
            lambda c: c not in ("]", "\n"),
        )

        if not section_name:
            raise self.parsing_error("Expected section name to be non-empty")

        self.expect("]")

        section = IniConfigSection(section_name)
        section.comment = comments

        self.parse_section_body(section)

        return section

    def parse_comments_only_document_edge_case(self, config: IniConfigBase):
        comment = self.parse_comments()

        self.expect_eof()

        config.unnamed_section.comment = comment

        return config

    def parse_normal(self, config: IniConfigBase):
        # parse unnamed section
        config.unnamed_section = IniConfigSection(None)
        self.parse_section_body(config.unnamed_section)

        # then any number of other sections
        sections = self.multiple(self.parse_section)

        for section in sections:
            assert section is not None

            if section.name in config.sections:
                raise self.parsing_error(
                    f'Section "{section.name}" was present multiple times'
                )

            config.sections[section.name] = section

        config.trailing_comment = self.parse_comments()

        self.expect_eof()

        return config

    def parse(self, config: IniConfigBase):
        self.choice(
            [
                functools.partial(self.parse_comments_only_document_edge_case, config),
                functools.partial(self.parse_normal, config),
            ]
        )


class IniParser:
    def __init__(self):
        self.allow_unquoted_values = True
        self.key_value_separator = "="
        self.comment_separator = "#"
        self.escape_character = "\\"
        self.quote_character = '"'
        self.escape_sequences = {
            r"\n": "\n",
            r"\t": "\t",
            r"\\": "\\",
            r"\"": '"',
        }
        self.new_line = "\n"

    @staticmethod
    def position_context(
        text_io: TextIOBase,
        position: int,
        context_lines: int = 1,
    ) -> Optional[PositionContext]:
        fd = text_io.fileno()

        # re-open file w/o automatic new-line conversion so that
        # position is relevant on platforms where new lines are of different
        # len from Unix style (LF)
        with open(
            fd,
            mode="r",
            encoding=text_io.encoding,
            newline="",
            closefd=False,
        ) as raw:
            raw.seek(0)

            read_bytes = 0
            lines = raw.readlines()

            for line_idx, line in enumerate(lines):
                line_size_bytes = len(line.encode(text_io.encoding))
                if position < read_bytes + line_size_bytes:
                    column_idx = 0
                    col_bytes = 0

                    # we found the line, now find which character specifically
                    while position > read_bytes + col_bytes + 1:
                        col_bytes += len(line[column_idx].encode(text_io.encoding))
                        column_idx += 1

                    return PositionContext(
                        line=line,
                        line_number=line_idx + 1,
                        column_number=column_idx + 1,
                        lines_before=lines[line_idx - context_lines : line_idx],
                    )

                read_bytes += line_size_bytes

            # edge case -- position points right after
            # the last character of the text
            if position == read_bytes:
                return PositionContext(
                    line=lines[-1],
                    line_number=line_idx + 1,
                    column_number=len(lines[-1]),
                    lines_before=lines[-1 - context_lines : -1],
                )

            # unable to determine
            return None

    def parse(
        self,
        text_io: TextIOBase,
        instance: IniConfigBase,
    ) -> None:
        parser = IniParserImpl(
            text_io,
            allow_unquoted_values=self.allow_unquoted_values,
            key_value_separator=self.key_value_separator,
            comment_separator=self.comment_separator,
            escape_character=self.escape_character,
            quote_character=self.quote_character,
            escape_sequences=self.escape_sequences,
            new_line=self.new_line,
        )

        try:
            parser.parse(instance)
        except ParsingError as err:
            effective: ParsingError = parser.deepest_error

            assert effective is not None

            position_context = self.position_context(
                text_io,
                effective.position,
            )

            if position_context:
                effective.position_context = position_context

                error_marker = "> "
                padding = " " * len(error_marker)

                position_message = padding + "..." + "\n"
                for line_before in position_context.lines_before:
                    position_message += padding + line_before

                position_message += error_marker
                position_message += position_context.line.rstrip("\n") + "\n"
                position_message += " " * (
                    position_context.column_number - 1 + len(error_marker)
                )
                position_message += "^\n"

                position_message += (
                    f"Line {position_context.line_number}, "
                    f"Column {position_context.column_number}, "
                    f"Byte {effective.position}\n"
                )

                effective.extend_message("\n\n" + position_message)

            raise effective from err
