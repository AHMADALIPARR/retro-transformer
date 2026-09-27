"""IR helpers: JSON emission for the retro transformer frontend."""

import json

from frontend.parser import parse_file, parse_source


def to_json(ir):
    """Serialize an IR dict to pretty JSON."""
    return json.dumps(ir, indent=2)


def write_ir(ir, path):
    """Write an IR dict to a .json file."""
    with open(path, "w") as f:
        f.write(to_json(ir) + "\n")


def load_ir(path):
    """Read an IR dict back from a .json file."""
    with open(path, "r") as f:
        return json.load(f)


__all__ = ["parse_file", "parse_source", "to_json", "write_ir", "load_ir"]
