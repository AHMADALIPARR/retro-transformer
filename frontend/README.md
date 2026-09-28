<!--
SPDX-License-Identifier: AGPL-3.0-or-later

retro-transformer
Copyright (C) 2026 SnapKitty Collective

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

# frontend — COBOL parser (Agent 1)

Hand-rolled COBOL-85 lexer + parser, stdlib only. Emits the IR
documented in `../IR_SCHEMA.md`.

```
frontend/
  lexer.py          fixed-format normalization, comments, tokenization
  parser.py         divisions/sections/paragraphs/statements -> IR dict
  ir.py             JSON emit/load helpers
  __main__.py       CLI: python -m frontend <file.cbl> [out.json]
  test_frontend.py  fixture tests (plain asserts)
```

Run the tests from the repo root:

```sh
python3 frontend/test_frontend.py
```

Parse one file:

```sh
python3 -m frontend fixtures/hello.cbl
```
