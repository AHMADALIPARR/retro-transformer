"""Chunking: split a parsed COBOL IR into translatable units.

The parser (Agent 1) produces an IR like::

    {"program": "NAME",
     "divisions": [{"name": "IDENTIFICATION",
                    "sections": [{"name": "...",
                                  "paragraphs": [{"name": "...",
                                                  "statements": [{"type": "DISPLAY",
                                                                  "text": "DISPLAY 'HELLO'",
                                                                  "line": 42}]}]}]}]}

One translation chunk is produced per paragraph. Every chunk carries the
same SharedContext: the program name plus all DATA division records, so the
model always sees the data layout the paragraph operates on.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Division whose statements describe data layout rather than logic.
DATA_DIVISION_NAMES = {"DATA", "DATA DIVISION"}


@dataclass
class SharedContext:
    """Information prepended to every chunk."""

    program: str = ""
    data_records: list[str] = field(default_factory=list)


@dataclass
class Chunk:
    """One translatable unit: a single paragraph plus shared context."""

    paragraph_name: str
    division: str
    section: str
    statements: list[dict]
    context: SharedContext

    @property
    def source_text(self) -> str:
        """The paragraph's COBOL source, one statement per line."""
        return "\n".join(
            str(stmt.get("text", "")) for stmt in self.statements
        )


def chunk_ir(ir: dict) -> list[Chunk]:
    """Split *ir* into one Chunk per paragraph.

    Args:
        ir: parsed program dict following the IR schema.

    Returns:
        List of Chunk, in document order. Paragraphs with no statements
        are skipped. Raises ValueError if the IR is malformed.
    """
    if not isinstance(ir, dict):
        raise ValueError(f"IR must be a dict, got {type(ir).__name__}")
    program = str(ir.get("program", ""))
    divisions = ir.get("divisions", [])
    if not isinstance(divisions, list):
        raise ValueError("IR 'divisions' must be a list")

    context = SharedContext(program=program)
    paragraphs: list[tuple[str, str, str, list[dict]]] = []

    for division in divisions:
        div_name = str(division.get("name", ""))
        for section in division.get("sections", []) or []:
            sec_name = str(section.get("name", ""))
            for paragraph in section.get("paragraphs", []) or []:
                par_name = str(paragraph.get("name", ""))
                statements = paragraph.get("statements", []) or []
                if _is_data_division(div_name):
                    context.data_records.extend(
                        str(stmt.get("text", ""))
                        for stmt in statements
                        if stmt.get("text")
                    )
                elif statements:
                    paragraphs.append((div_name, sec_name, par_name, statements))

    return [
        Chunk(
            paragraph_name=par_name,
            division=div_name,
            section=sec_name,
            statements=statements,
            context=context,
        )
        for div_name, sec_name, par_name, statements in paragraphs
    ]


def format_context(context: SharedContext) -> str:
    """Render the shared context as a prompt-friendly text block."""
    lines = [f"Program: {context.program or '<unnamed>'}", ""]
    lines.append("DATA DIVISION records:")
    if context.data_records:
        lines.extend(f"    {rec}" for rec in context.data_records)
    else:
        lines.append("    (none)")
    return "\n".join(lines)


def _is_data_division(name: str) -> bool:
    return name.strip().upper() in DATA_DIVISION_NAMES
