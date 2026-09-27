"""Retro Transformer — transformation engine.

Converts a parsed COBOL intermediate representation (IR) into modern
source code (Java / Python) using IBM watsonx.ai Granite models.

Modules:
    watsonx     watsonx.ai REST client (IAM auth, text generation, retry/backoff)
    chunking    splits the IR into per-paragraph translation chunks
    prompts     prompt templates for Granite code models (COBOL->Java, COBOL->Python)
    transform   orchestration: chunk -> prompt -> model -> assembled file,
                plus a MOCK=1 mode for credential-free testing

The real watsonx.ai path is gated behind environment variables and is never
attempted when MOCK=1.
"""

from .chunking import Chunk, SharedContext, chunk_ir, format_context
from .prompts import (
    TARGETS,
    build_cobol_to_java_prompt,
    build_cobol_to_python_prompt,
    build_prompt,
)
from .transform import (
    is_mock_mode,
    transform_program,
    translate_chunk,
    write_output,
)
from .watsonx import (
    MissingCredentialsError,
    WatsonxClient,
    WatsonxConfig,
    WatsonxError,
)

__all__ = [
    "Chunk",
    "SharedContext",
    "chunk_ir",
    "format_context",
    "TARGETS",
    "build_prompt",
    "build_cobol_to_java_prompt",
    "build_cobol_to_python_prompt",
    "is_mock_mode",
    "transform_program",
    "translate_chunk",
    "write_output",
    "MissingCredentialsError",
    "WatsonxClient",
    "WatsonxConfig",
    "WatsonxError",
]
