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

# retro transformer

Turn legacy COBOL into modern Java or Python with IBM watsonx.ai Granite
models. Built for the IBM hackathon stack: **watsonx.ai + Granite** for the
transform, **Code Engine** for deployment, **Cloud Object Storage** for
artifacts.

## Architecture

```
                  IR (JSON)                 per-paragraph chunks
  HELLO.cbl  ┌──────────────┐  ┌─────────────────────┐  ┌──────────────┐
 ───────────▶│   frontend   │─▶│      pipeline       │─▶│    engine    │
             │  (COBOL → IR)│  │    `retro` CLI       │  │ watsonx.ai   │
             └──────────────┘  │  parse → transform  │  │   Granite    │
                               └─────────┬───────────┘  └──────────────┘
                                         │ out/<program>/
                                  ┌──────▼──────┐
                                  │   deploy    │──▶ Code Engine job
                                  │ Dockerfile  │    + COS buckets
                                  └─────────────┘
```

| Area         | Owner   | Contents |
|--------------|---------|----------|
| `frontend/`  | Agent 1 | COBOL parser → IR |
| `engine/`    | Agent 2 | chunking, prompts, watsonx.ai client, mock mode |
| `pipeline/`  | Agent 3 | `retro` CLI (parse / transform) |
| `deploy/`    | Agent 3 | Dockerfile + Code Engine runbook |
| `tests/`     | Agent 3 | end-to-end mock-mode tests |
| `fixtures/`  | Agent 1 | sample `.cbl` programs |

IR schema (contract between frontend and engine):

```json
{"program": "NAME", "divisions": [
  {"name": "...", "sections": [
    {"name": "...", "paragraphs": [
      {"name": "...", "statements": [
        {"type": "DISPLAY", "text": "...", "line": 42}]}]}]}]}
```

## Quickstart (zero credentials)

```sh
# parse a COBOL file to IR
python3 pipeline/retro parse fixtures/HELLO.cbl

# full mock transform (no network, no credentials)
python3 pipeline/retro transform fixtures/HELLO.cbl --to java --mock
python3 pipeline/retro transform fixtures/HELLO.cbl --to python --mock
# outputs land in out/HELLO/

# run the end-to-end suite
python3 tests/test_e2e.py
```

Mock mode is forced by `--mock`, by `MOCK=1` in the environment, or
automatically when no watsonx.ai credentials are set.

## Going live with real watsonx.ai credentials

```sh
export WATSONX_API_KEY='<ibm-cloud-api-key>'
export WATSONX_PROJECT_ID='<watsonx-project-id>'
export WATSONX_REGION=us-south                    # optional
export WATSONX_MODEL_ID=ibm/granite-3-8b-instruct # optional

python3 pipeline/retro transform fixtures/HELLO.cbl --to java
```

With credentials present and no `--mock`, `retro` calls the real Granite
model through `engine/`. Never commit these values; use environment
variables or a Code Engine secret.

## Deploy

See [deploy/code-engine.md](deploy/code-engine.md) for the full runbook:
build the image from `deploy/Dockerfile`, create a Code Engine job, submit
jobruns per COBOL program, attach watsonx.ai credentials as a secret, and
wire Cloud Object Storage buckets (`retro-in` / `retro-out`) for artifacts.

## Layout

```
retro-transformer/
├── pipeline/retro        # CLI: parse | transform --to java|python [--mock]
├── engine/               # chunking, prompts, watsonx client, mock engine
├── frontend/             # COBOL → IR parser
├── fixtures/             # sample .cbl programs
├── deploy/
│   ├── Dockerfile        # python:3.12-slim, entrypoint = retro
│   └── code-engine.md    # ibmcloud runbook + COS wiring
├── tests/test_e2e.py     # mock-mode end-to-end tests (stdlib only)
└── out/                  # generated outputs (git-ignored)
```

Python 3, standard library only. No frameworks, no lockfiles.

## License

AGPL-3.0-or-later — see [LICENSE](LICENSE). Every source file carries
an SPDX header (`SPDX-License-Identifier: AGPL-3.0-or-later`).
Copyright (C) 2026 SnapKitty Collective.
