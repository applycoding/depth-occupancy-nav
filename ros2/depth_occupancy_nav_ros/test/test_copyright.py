# Copyright 2026 Arpan Bom
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

from pathlib import Path

import pytest
from ament_copyright.main import main


@pytest.mark.copyright
@pytest.mark.linter
def test_copyright() -> None:
    root = Path(__file__).resolve().parents[1]
    rc = main(
        argv=[
            str(root / "depth_occupancy_nav_ros"),
            str(root / "launch"),
            str(root / "test"),
            str(root / "config"),
            str(root / "package.xml"),
        ]
    )
    assert rc == 0, "Found errors"
