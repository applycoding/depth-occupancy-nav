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

"""Pytest hooks for ROS package tests (host vs Jazzy image)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2].parent
_SRC = _ROOT / "src"
_PKG = Path(__file__).resolve().parents[1]
for p in (str(_SRC), str(_PKG)):
    if p not in sys.path:
        sys.path.insert(0, p)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    try:
        import launch_pytest  # noqa: F401
    except ImportError:
        skip_launch = pytest.mark.skip(reason="launch_pytest not available (run in ROS Jazzy image)")
        for item in items:
            if "test_launch" in item.nodeid:
                item.add_marker(skip_launch)
    try:
        import ament_copyright  # noqa: F401
    except ImportError:
        skip_cr = pytest.mark.skip(reason="ament_copyright not available (ROS ament)")
        for item in items:
            if "test_copyright" in item.nodeid:
                item.add_marker(skip_cr)
