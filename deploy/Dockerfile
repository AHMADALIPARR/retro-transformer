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

# retro transformer -- Code Engine deployment image
FROM python:3.12-slim

WORKDIR /app

# stdlib-only: no pip install needed
COPY . /app

RUN chmod +x /app/pipeline/retro

# Run as a Code Engine job; pass the retro subcommand as job args, e.g.:
#   transform /data/HELLO.cbl --to java --mock
ENTRYPOINT ["python3", "/app/pipeline/retro"]
CMD ["--help"]
