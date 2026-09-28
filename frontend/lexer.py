# SPDX-License-Identifier: AGPL-3.0-or-later
#
# retro-transformer
# Copyright (C) 2026 SnapKitty Collective
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

"""COBOL lexer for the retro transformer frontend.

Pragmatic, not GnuCOBOL: fixed-format normalization (sequence numbers,
column-7 indicators, continuations), comment stripping, and tokenization
with source line tracking. Every token remembers where it came from so
the parser can slice exact statement text and line numbers.
"""

import re

_TOKEN_RE = re.compile(r"""
      (?P<string>'[^']*'|"[^"]*")        # quoted literal
    | (?P<word>[A-Za-z0-9][A-Za-z0-9_\-]*)  # names, keywords (may start w/ digit: 100-INIT)
    | (?P<number>\d+(?:\.\d+)?)          # numeric literal (3.14 stays one token)
    | (?P<punct>[(),;:.])                # punctuation
    | (?P<other>[^\s])                    # operators etc: = > < + - * /
""", re.VERBOSE)


class Token:
    """A lexical token with its source position."""

    __slots__ = ("kind", "text", "upper", "lineno", "li", "start", "end")

    def __init__(self, kind, text, lineno, li, start, end):
        self.kind = kind            # word | number | string | punct | other
        self.text = text            # exact spelling from source
        self.upper = text.upper() if kind == "word" else text
        self.lineno = lineno        # 1-based source line number
        self.li = li                # index into the logical-line list
        self.start = start          # char offset in the logical line
        self.end = end

    def __repr__(self):
        return "Token(%r, %r, line=%d)" % (self.kind, self.text, self.lineno)


def normalize_lines(source):
    """Split source into logical lines: [(text, lineno)].

    - Drops blank lines and comments (``*>`` free-format, ``*``/``/``
      in column 7 of fixed-format lines, ``* `` free-format lines).
    - Fixed-format lines (digit/blank sequence area in cols 1-6) are
      cut to columns 7-72.
    - Continuation lines (``-`` in column 7) are joined onto the
      previous logical line.
    """
    logical = []
    for lineno, raw in enumerate(source.splitlines(), start=1):
        if not raw.strip():
            continue
        stripped = raw.lstrip()
        if stripped.startswith("*>"):
            continue
        fixed = len(raw) >= 7 and all(c == " " or c.isdigit() for c in raw[:6])
        if fixed:
            indicator = raw[6]
            if indicator in "*/":
                continue
            if indicator == "-":
                cont = raw[7:72] if len(raw) > 7 else ""
                if logical:
                    prev_text, prev_line = logical[-1]
                    logical[-1] = (prev_text + cont, prev_line)
                continue
            content = raw[6:72] if len(raw) > 6 else ""
        else:
            if stripped.startswith("*") and (
                len(stripped) == 1 or stripped[1] in " \t"
            ):
                continue
            content = raw[:72]
        logical.append((content, lineno))
    return logical


def tokenize(line_text, lineno, li):
    """Tokenize one logical line, tagging each token with its position."""
    toks = []
    for m in _TOKEN_RE.finditer(line_text):
        toks.append(Token(m.lastgroup, m.group(), lineno, li,
                          m.start(), m.end()))
    return toks
