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

"""Pragmatic COBOL-85 parser -> IR dict for the retro transformer.

Handles the four divisions, sections, paragraphs, and the common
statement verbs. Statement text is sliced from the original source so
it is reproduced exactly; ``line`` is the 1-based source line where
the statement starts.

Deliberate simplifications (documented in IR_SCHEMA.md):
- The token stream is split at every verb keyword, so IF/ELSE/END-IF
  (and friends) appear as sibling statements in source order.
- DATA division entries become paragraphs (one per 01/77/FD/SD record)
  with each data-description line as a ``DATA`` statement.
"""

from frontend.lexer import normalize_lines, tokenize

DIVISIONS = ("IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE")

# Statement-starting verbs. Any of these begins a new statement entry.
VERBS = {
    "DISPLAY", "MOVE", "ADD", "SUBTRACT", "MULTIPLY", "DIVIDE", "COMPUTE",
    "IF", "ELSE", "PERFORM", "GO", "STOP", "OPEN", "READ", "WRITE",
    "CLOSE", "CALL", "COPY", "ACCEPT", "EVALUATE", "CONTINUE", "EXIT",
    "WHEN", "OTHER",
    "END-IF", "END-PERFORM", "END-READ", "END-WRITE", "END-EVALUATE",
    "END-COMPUTE", "END-ADD", "END-SUBTRACT", "END-MULTIPLY",
    "END-DIVIDE", "END-CALL", "END-SEARCH",
    "SET", "SEARCH", "SORT", "MERGE", "STRING", "UNSTRING", "INSPECT",
    "ALTER", "NEXT", "GOBACK", "RETURN", "RELEASE", "REWRITE",
    "DELETE", "START", "USE",
}

# Paragraph headers allowed outside PROCEDURE division.
HEADER_KEYWORDS = {
    "PROGRAM-ID", "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "SOURCE-COMPUTER", "OBJECT-COMPUTER", "REPOSITORY",
    "FILE-CONTROL", "I-O-CONTROL",
}

# DATA-division levels that open a new record paragraph.
DATA_NEW_RECORD_LEVELS = {1, 77}


class Parser:
    def __init__(self, logical):
        self.logical = logical
        self.toks = []
        for li, (text, lineno) in enumerate(logical):
            self.toks.extend(tokenize(text, lineno, li))
        self.i = 0
        self.div = None
        self.sec = None
        self.para = None
        self.divisions = []

    # ------------------------------------------------------------------
    # navigation
    # ------------------------------------------------------------------
    def peek(self, k=0):
        j = self.i + k
        return self.toks[j] if 0 <= j < len(self.toks) else None

    def skip_dot(self):
        t = self.peek()
        if t is not None and t.text == ".":
            self.i += 1

    @staticmethod
    def is_terminator(tok):
        # A bare '.' ends a statement. (Decimal literals like 3.14 are
        # single tokens, so they never trip this.)
        return tok.text == "." or (
            len(tok.text) > 1 and tok.text.endswith(".")
        )

    def scan_to_dot(self, start):
        """Index just past the terminating '.' (or end of tokens)."""
        j = start
        while j < len(self.toks):
            if self.is_terminator(self.toks[j]):
                return j + 1
            j += 1
        return j

    def slice_text(self, first_idx, past_idx):
        """Exact source text spanned by tokens [first_idx, past_idx),
        minus any trailing statement-terminating period."""
        toks = self.toks
        end = past_idx
        if end > first_idx and toks[end - 1].text == ".":
            end -= 1
        if end <= first_idx:
            return ""
        first, last = toks[first_idx], toks[end - 1]
        parts = []
        for li in range(first.li, last.li + 1):
            line = self.logical[li][0]
            s = first.start if li == first.li else 0
            e = last.end if li == last.li else len(line)
            parts.append(line[s:e].strip())
        text = " ".join(p for p in parts if p).strip()
        if text.endswith("."):
            text = text[:-1].rstrip()
        return text

    # ------------------------------------------------------------------
    # structure builders
    # ------------------------------------------------------------------
    def new_division(self, name):
        self.div = {"name": name, "sections": []}
        self.divisions.append(self.div)
        self.new_section("MAIN")

    def new_section(self, name):
        if self.div is None:
            self.new_division("UNKNOWN")
        self.sec = {"name": name, "paragraphs": []}
        self.div["sections"].append(self.sec)
        self.para = None

    def new_paragraph(self, name):
        if self.sec is None:
            self.new_section("MAIN")
        self.para = {"name": name, "statements": []}
        self.sec["paragraphs"].append(self.para)

    def ensure_para(self):
        if self.para is None:
            self.new_paragraph("ANON")

    def add_statement(self, stype, text, line):
        self.ensure_para()
        self.para["statements"].append(
            {"type": stype, "text": text, "line": line}
        )

    # ------------------------------------------------------------------
    # grammar pieces
    # ------------------------------------------------------------------
    def parse_data_entry(self):
        """FD/SD or level-number entry in the DATA division."""
        t = self.peek()
        if t is None:
            return False
        if t.kind == "word" and t.upper in ("FD", "SD"):
            end = self.scan_to_dot(self.i)
            label = " ".join(
                tok.text for tok in self.toks[self.i + 1:end]
                if tok.text != "."
            )
            name = (t.upper + " " + label).strip()
            text = self.slice_text(self.i, end)
            self.new_paragraph(name)
            self.add_statement("DATA", text, t.lineno)
            self.i = end
            return True
        if t.kind in ("number", "word") and t.text.isdigit():
            level = int(t.text)
            end = self.scan_to_dot(self.i)
            label = " ".join(
                tok.text for tok in self.toks[self.i + 1:end]
                if tok.text != "."
            )
            text = self.slice_text(self.i, end)
            if level in DATA_NEW_RECORD_LEVELS:
                self.new_paragraph(("%02d %s" % (level, label)).strip())
            self.add_statement("DATA", text, t.lineno)
            self.i = end
            return True
        return False

    def parse_paragraph_header(self):
        """A line of the form NAME. that opens a paragraph."""
        t = self.peek()
        nxt = self.peek(1)
        if t is None or t.kind != "word" or nxt is None or nxt.text != ".":
            return False
        up = t.upper
        if up in VERBS or up in ("DIVISION", "SECTION"):
            return False
        divname = self.div["name"] if self.div else ""
        if divname == "PROCEDURE":
            self.new_paragraph(t.text)
            self.i += 2
            return True
        if divname in ("IDENTIFICATION", "ENVIRONMENT") \
                and up in HEADER_KEYWORDS:
            self.new_paragraph(up)
            self.i += 2
            return True
        return False

    def parse_statement(self):
        t = self.peek()
        up = t.upper
        if up == "GO" and self.peek(1) is not None \
                and self.peek(1).upper == "TO":
            stype = "GO TO"
        elif up in VERBS:
            stype = up
        else:
            stype = "CLAUSE"  # non-verb line (PROGRAM-ID value, SELECT, ...)
        start = self.i
        j = self.i
        while j < len(self.toks):
            tj = self.toks[j]
            if j > start and tj.kind == "word" and tj.upper in VERBS:
                break  # next statement starts here
            if self.is_terminator(tj):
                break
            j += 1
        past = j + 1 if j < len(self.toks) and self.is_terminator(
            self.toks[j]) else j
        text = self.slice_text(start, past)
        self.add_statement(stype, text, t.lineno)
        self.i = past

    # ------------------------------------------------------------------
    # driver
    # ------------------------------------------------------------------
    def parse(self):
        while self.i < len(self.toks):
            t = self.peek()
            nxt = self.peek(1)
            if t.upper in DIVISIONS and nxt is not None \
                    and nxt.upper == "DIVISION":
                self.new_division(t.upper)
                self.i += 2
                self.skip_dot()
                continue
            if t.kind == "word" and nxt is not None \
                    and nxt.upper == "SECTION":
                self.new_section(t.text.upper())
                self.i += 2
                self.skip_dot()
                continue
            if self.div is not None and self.div["name"] == "DATA" \
                    and self.parse_data_entry():
                continue
            if self.parse_paragraph_header():
                continue
            self.parse_statement()
        return {"program": self.program_name(),
                "divisions": self.divisions}

    def program_name(self):
        for d in self.divisions:
            if d["name"] == "IDENTIFICATION":
                for s in d["sections"]:
                    for p in s["paragraphs"]:
                        if p["name"] == "PROGRAM-ID" and p["statements"]:
                            return p["statements"][0]["text"].strip(
                                " \t'\"")
        return "UNKNOWN"


def parse_source(source):
    """Parse COBOL source text -> IR dict."""
    return Parser(normalize_lines(source)).parse()


def parse_file(path):
    """Parse a .cbl file -> IR dict."""
    with open(path, "r") as f:
        return parse_source(f.read())
