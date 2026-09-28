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

"""CLI: parse a COBOL file and print (or save) its IR as JSON.

Usage:
    python -m frontend fixtures/hello.cbl
    python -m frontend fixtures/hello.cbl /tmp/hello.json
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.parser import parse_file
from frontend.ir import to_json


def main(argv):
    if len(argv) < 2:
        print("usage: python -m frontend <file.cbl> [out.json]",
              file=sys.stderr)
        return 2
    ir = parse_file(argv[1])
    out = to_json(ir)
    if len(argv) > 2:
        with open(argv[2], "w") as f:
            f.write(out + "\n")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
