#!/usr/bin/env python3
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

"""End-to-end tests for the retro transformer (Agent 3).

Runs the full pipeline in mock mode over every fixture in fixtures/ and
asserts the outputs exist and contain the expected markers.

Plain asserts only -- no test framework, no credentials, no network.
Exit 0 when everything passes, 1 otherwise.
"""

import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETRO = [sys.executable, os.path.join(ROOT, "pipeline", "retro")]
FIXTURES = os.path.join(ROOT, "fixtures")
OUT = os.path.join(ROOT, "out")

failures = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"{tag}  {name}")
    if not cond:
        failures.append(name)
        if detail:
            print(f"       {detail[:400]}")


def run(*args):
    return subprocess.run(
        RETRO + list(args), capture_output=True, text=True, cwd=ROOT
    )


def out_files(program):
    found = []
    outdir = os.path.join(OUT, program)
    for dirpath, _, filenames in os.walk(outdir):
        found.extend(os.path.join(dirpath, f) for f in filenames)
    return outdir, found


def main():
    cbls = sorted(
        f for f in os.listdir(FIXTURES) if f.lower().endswith(".cbl")
    )
    check("fixtures directory has .cbl files", len(cbls) > 0,
          f"found in {FIXTURES}")

    # --- transform: java + python, mock mode, every fixture ---
    # markers match the engine's deterministic mock output
    for target, marker, ext in (("java", "public static void", ".java"),
                                ("python", "def ", ".py")):
        for cbl in cbls:
            program = os.path.splitext(cbl)[0].upper()
            shutil.rmtree(os.path.join(OUT, program), ignore_errors=True)

            r = run("transform", os.path.join("fixtures", cbl),
                    "--to", target, "--mock")
            check(f"transform {cbl} -> {target}: exit 0", r.returncode == 0,
                  r.stderr)

            outdir, files = out_files(program)
            code_files = [p for p in files if p.endswith(ext)]
            check(f"transform {cbl} -> {target}: output file(s) written "
                  f"under out/{program}/", len(code_files) > 0,
                  f"files: {files}")

            blob = ""
            for p in files:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    blob += fh.read() + "\n"
            check(f"transform {cbl} -> {target}: contains '{marker}' marker",
                  marker in blob)
            check(f"transform {cbl} -> {target}: references program {program}",
                  program in blob or program.lower() in blob.lower())
            check(f"transform {cbl} -> {target}: ir.json trace written",
                  os.path.isfile(os.path.join(outdir, "ir.json")))

    # --- parse contract: valid IR JSON with program + divisions ---
    cbl = cbls[0]
    r = run("parse", os.path.join("fixtures", cbl))
    try:
        ir = json.loads(r.stdout)
        ok = (isinstance(ir, dict) and isinstance(ir.get("program"), str)
              and isinstance(ir.get("divisions"), list))
    except Exception:  # noqa: BLE001
        ok = False
    check("parse: emits IR JSON honoring the schema "
          "(program, divisions[])", r.returncode == 0 and ok, r.stderr)

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for name in failures:
            print(f"  - {name}")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
