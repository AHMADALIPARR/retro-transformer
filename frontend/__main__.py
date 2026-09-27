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
