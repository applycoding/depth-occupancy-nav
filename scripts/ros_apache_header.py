# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""One-shot: stamp ROS package Python sources with the ament Apache header."""

from __future__ import annotations

from pathlib import Path

HEADER = """# Copyright 2026 Arpan Bom
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""

ROOT = Path(__file__).resolve().parents[1] / "ros2" / "depth_occupancy_nav_ros"


def strip_header(text: str) -> str:
    lines = text.splitlines(keepends=True)
    idx = 0
    while idx < len(lines) and (
        lines[idx].startswith("#")
        or lines[idx].strip() == ""
        or lines[idx].startswith('"""')
        or lines[idx].startswith("'''")
    ):
        if lines[idx].startswith('"""') or lines[idx].startswith("'''"):
            break
        idx += 1
    return "".join(lines[idx:])


def main() -> None:
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in {".pytest_cache", "build", "install"} for part in path.parts):
            continue
        body = strip_header(path.read_text(encoding="utf-8"))
        path.write_text(HEADER + "\n" + body.lstrip("\n"), encoding="utf-8")
    print("updated", len(list(ROOT.rglob("*.py"))), "files")


if __name__ == "__main__":
    main()
