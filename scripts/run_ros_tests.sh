#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Run ROS launch tests inside the digest-pinned Jazzy image (same steps as CI ros job).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="ros:jazzy-ros-base@sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617"
NAV2_NAVFN_VER="${NAV2_NAVFN_VER:-1.3.13-1noble.20260921.031752}"
NAV2_PLANNER_VER="${NAV2_PLANNER_VER:-1.3.13-1noble.20260921.031801}"
docker run --rm --init --platform linux/amd64 \
  -v "$ROOT:/ws" -w /ws "$IMAGE" bash -lc "
    set -eo pipefail
    set +u
    source /opt/ros/jazzy/setup.bash
    set -u
    apt-get update -qq || true
    dpkg -i /ws/ros-debs/*.deb || apt-get -f install -y -qq
    NAVFN_VER=\$(dpkg-query -W ros-jazzy-nav2-navfn-planner | cut -f2)
    PLANNER_VER=\$(dpkg-query -W ros-jazzy-nav2-planner | cut -f2)
    test \"\$NAVFN_VER\" = \"${NAV2_NAVFN_VER}\"
    test \"\$PLANNER_VER\" = \"${NAV2_PLANNER_VER}\"
    dpkg-query -W > /ws/apt-versions.txt
    python3 /ws/get-pip.py --break-system-packages
    python3 -m pip install -q --break-system-packages --no-index -f /ws/wheelhouse \\
      --ignore-installed numpy==2.5.4 pillow==13.0.0 pytest==9.2.0
    export PYTHONPATH=\"/ws/src:\${PYTHONPATH:-}\"
    cd /ws/ros2/depth_occupancy_nav_ros
    colcon build --packages-select depth_occupancy_nav_ros
    set +u
    . install/setup.bash
    set -u
    export DO_REQUIRE_ROS=1
    collect_out=\$(python3 -m pytest --collect-only -q 2>&1) || { echo \"\$collect_out\"; exit 1; }
    echo \"\$collect_out\"
    collected=\$(echo \"\$collect_out\" | grep ' tests collected' | tail -1 | sed -n 's/^\\([0-9][0-9]*\\) tests collected.*/\\1/p')
    if [ -z \"\$collected\" ] || [ \"\$collected\" -lt 42 ]; then
      echo \"expected at least 42 ROS tests collected, got \${collected:-0}\"
      exit 1
    fi
    out=\$(python3 -m pytest -q -rs 2>&1) || { echo \"\$out\"; exit 1; }
    echo \"\$out\"
    if echo \"\$out\" | grep -qE '[1-9][0-9]* skipped'; then
      echo \"unexpected pytest skips\"
      exit 1
    fi
  "
