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
