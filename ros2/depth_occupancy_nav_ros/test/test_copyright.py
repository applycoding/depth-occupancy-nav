# Copyright 2026 Arpan Bom
# SPDX-License-Identifier: Apache-2.0
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
            str(root / "setup.py"),
        ]
    )
    assert rc == 0, "Found errors"
