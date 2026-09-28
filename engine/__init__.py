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
