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

"""Fixture tests for the COBOL frontend.

Parses every fixture in ../fixtures/ and asserts the IR matches the
expected structure. Plain asserts with clear output -- no framework.
Run from anywhere:  python3 frontend/test_frontend.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from frontend.parser import parse_file
from frontend.ir import to_json
import json

FIX = os.path.join(ROOT, "fixtures")
passed = 0


def check(name, cond, detail=""):
    global passed
    if not cond:
        print("[FAIL] %s %s" % (name, detail))
        sys.exit(1)
    passed += 1
    print("[ok]   %s" % name)


def div(ir, name):
    for d in ir["divisions"]:
        if d["name"] == name:
            return d
    return None


def section(d, name):
    for s in d["sections"]:
        if s["name"] == name:
            return s
    return None


def paragraph(s, name):
    for p in s["paragraphs"]:
        if p["name"] == name:
            return p
    return None


def stmt_types(paras):
    return [st["type"] for p in paras for st in p["statements"]]


# ---------------------------------------------------------------- hello
ir = parse_file(os.path.join(FIX, "hello.cbl"))
check("hello: program name", ir["program"] == "HELLO", repr(ir["program"]))
check("hello: divisions",
      [d["name"] for d in ir["divisions"]] == ["IDENTIFICATION", "PROCEDURE"])
proc = div(ir, "PROCEDURE")
paras = proc["sections"][0]["paragraphs"]
check("hello: one paragraph", len(paras) == 1 and paras[0]["name"] == "MAIN-LOGIC")
check("hello: statement types",
      stmt_types(paras) == ["DISPLAY", "STOP"], str(stmt_types(paras)))
disp = paras[0]["statements"][0]
check("hello: DISPLAY text/line",
      disp["text"] == "DISPLAY 'HELLO, WORLD'" and disp["line"] == 5,
      repr(disp))

# -------------------------------------------------------------- payroll
ir = parse_file(os.path.join(FIX, "payroll.cbl"))
check("payroll: program name", ir["program"] == "PAYROLL")
check("payroll: four divisions",
      [d["name"] for d in ir["divisions"]] ==
      ["IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE"])
data = div(ir, "DATA")
ws = section(data, "WORKING-STORAGE")
check("payroll: WORKING-STORAGE section", ws is not None)
rec = paragraph(ws, "01 PAY-RECORD")
check("payroll: 01 PAY-RECORD paragraph", rec is not None)
check("payroll: record has 5 DATA statements",
      len(rec["statements"]) == 5 and
      all(s["type"] == "DATA" for s in rec["statements"]),
      str(rec["statements"]))
check("payroll: field text preserved",
      rec["statements"][1]["text"] == "05 EMP-NAME      PIC X(20).".rstrip("."),
      repr(rec["statements"][1]["text"]))
proc = div(ir, "PROCEDURE")
p_main = paragraph(proc["sections"][0], "MAIN-LOGIC")
p_calc = paragraph(proc["sections"][0], "CALC-PAY")
check("payroll: two paragraphs", p_main is not None and p_calc is not None)
check("payroll: PERFORM loop",
      p_main["statements"][0]["type"] == "PERFORM" and
      "TIMES" in p_main["statements"][0]["text"],
      repr(p_main["statements"][0]))
check("payroll: CALC-PAY statement flow",
      stmt_types([p_calc]) ==
      ["ADD", "COMPUTE", "IF", "DISPLAY", "ELSE", "DISPLAY", "END-IF", "ADD"],
      str(stmt_types([p_calc])))
check("payroll: COMPUTE text",
      p_calc["statements"][1]["text"] == "COMPUTE EMP-GROSS = EMP-HOURS * EMP-RATE",
      repr(p_calc["statements"][1]["text"]))

# --------------------------------------------------------------- fileio
ir = parse_file(os.path.join(FIX, "fileio.cbl"))
check("fileio: program name", ir["program"] == "FILEIO")
env = div(ir, "ENVIRONMENT")
check("fileio: INPUT-OUTPUT section",
      section(env, "INPUT-OUTPUT") is not None)
fc = paragraph(section(env, "INPUT-OUTPUT"), "FILE-CONTROL")
check("fileio: SELECT is a CLAUSE",
      fc["statements"][0]["type"] == "CLAUSE" and
      "SELECT PAY-FILE" in fc["statements"][0]["text"],
      repr(fc["statements"][0]))
data = div(ir, "DATA")
fs = section(data, "FILE")
check("fileio: FILE SECTION", fs is not None)
fd = paragraph(fs, "FD PAY-FILE")
check("fileio: FD paragraph", fd is not None)
check("fileio: 01 PAY-REC under FD",
      paragraph(fs, "01 PAY-REC") is not None)
proc = div(ir, "PROCEDURE")
p_main = paragraph(proc["sections"][0], "MAIN-LOGIC")
p_read = paragraph(proc["sections"][0], "READ-LOOP")
check("fileio: OPEN/READ/WRITE/CLOSE verbs present",
      {"OPEN", "READ", "CLOSE"} <= set(stmt_types([p_main, p_read])),
      str(stmt_types([p_main, p_read])))
check("fileio: MAIN-LOGIC flow",
      stmt_types([p_main]) == ["OPEN", "PERFORM", "CLOSE", "STOP"],
      str(stmt_types([p_main])))
check("fileio: READ-LOOP flow",
      stmt_types([p_read]) ==
      ["READ", "MOVE", "END-READ", "IF", "DISPLAY", "END-IF"],
      str(stmt_types([p_read])))
check("fileio: PERFORM UNTIL text",
      "UNTIL" in p_main["statements"][1]["text"],
      repr(p_main["statements"][1]["text"]))

# ------------------------------------------------------- schema shape
ir = parse_file(os.path.join(FIX, "hello.cbl"))
blob = json.loads(to_json(ir))  # JSON round-trip
check("schema: top-level keys", set(blob.keys()) == {"program", "divisions"})
d0 = blob["divisions"][0]
check("schema: division keys", set(d0.keys()) == {"name", "sections"})
s0 = d0["sections"][0]
check("schema: section keys", set(s0.keys()) == {"name", "paragraphs"})
p0 = blob["divisions"][1]["sections"][0]["paragraphs"][0]
check("schema: paragraph keys", set(p0.keys()) == {"name", "statements"})
st0 = p0["statements"][0]
check("schema: statement keys", set(st0.keys()) == {"type", "text", "line"})
check("schema: line is int", isinstance(st0["line"], int))

print("\nAll %d checks passed." % passed)
