"""Prompt templates for Granite code models.

Each builder takes a Chunk (one COBOL paragraph + shared context) and
returns the full prompt string sent to watsonx.ai text generation.

The templates instruct:
  * faithful semantic translation -- preserve behavior, not just syntax
  * idiomatic target-language output (no COBOL-isms like GOTO chains)
  * data items mapped to sensible types using the DATA division context
  * output ONLY the translated code, wrapped in a fenced code block
"""

from __future__ import annotations

from .chunking import Chunk, format_context

JAVA = "java"
PYTHON = "python"
TARGETS = (JAVA, PYTHON)


def build_prompt(chunk: Chunk, target: str) -> str:
    """Dispatch to the per-target prompt builder."""
    target = target.lower()
    if target == JAVA:
        return build_cobol_to_java_prompt(chunk)
    if target == PYTHON:
        return build_cobol_to_python_prompt(chunk)
    raise ValueError(f"Unsupported target {target!r}; expected one of {TARGETS}")


def build_cobol_to_java_prompt(chunk: Chunk) -> str:
    """Prompt for COBOL -> idiomatic Java translation of one paragraph."""
    return f"""You are an expert COBOL-to-Java modernization engine. Translate the
COBOL paragraph below into idiomatic Java 17.

Rules:
1. Preserve the exact behavior (semantics) of the COBOL code. Do not invent
   new behavior, drop edge cases, or reorder observable side effects.
2. Write idiomatic Java 17: meaningful method and variable names, proper
   types, no GOTO-style control flow, no COBOL-isms in comments.
3. Map COBOL data items to Java types sensibly:
   - PIC 9 numeric -> int / long / BigDecimal (BigDecimal for decimals)
   - PIC X / alphanumeric -> String
   - level-88 condition names -> boolean helpers or enums
   State any assumptions in a brief header comment.
4. Translate DISPLAY to System.out.println, ACCEPT to console/Scanner input
   only if the paragraph reads input; otherwise keep it a pure method.
5. Output ONLY the Java code, wrapped in a single ```java fenced block.
   No explanations before or after the block.

{format_context(chunk.context)}

COBOL paragraph "{chunk.paragraph_name}" (from {chunk.division} / {chunk.section}):

```cobol
{chunk.source_text}
```
"""


def build_cobol_to_python_prompt(chunk: Chunk) -> str:
    """Prompt for COBOL -> idiomatic Python translation of one paragraph."""
    return f"""You are an expert COBOL-to-Python modernization engine. Translate the
COBOL paragraph below into idiomatic Python 3.

Rules:
1. Preserve the exact behavior (semantics) of the COBOL code. Do not invent
   new behavior, drop edge cases, or reorder observable side effects.
2. Write idiomatic Python 3: snake_case names, type hints, dataclasses for
   COBOL records where sensible, no GOTO-style control flow.
3. Map COBOL data items to Python types sensibly:
   - PIC 9 numeric -> int, PIC 9V9... decimals -> Decimal
   - PIC X / alphanumeric -> str
   - level-88 condition names -> booleans or Enum
   State any assumptions in a brief module docstring comment.
4. Translate DISPLAY to print(); keep I/O at the edges so the core logic is
   a pure, testable function.
5. Output ONLY the Python code, wrapped in a single ```python fenced block.
   No explanations before or after the block.

{format_context(chunk.context)}

COBOL paragraph "{chunk.paragraph_name}" (from {chunk.division} / {chunk.section}):

```cobol
{chunk.source_text}
```
"""
