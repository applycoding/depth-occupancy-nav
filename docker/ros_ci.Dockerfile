# SPDX-License-Identifier: Apache-2.0
FROM ros:jazzy-ros-base@sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617

RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    python3-pip python3-venv \
    ros-jazzy-nav2-navfn-planner \
    ros-jazzy-nav2-planner \
    ros-jazzy-nav2-costmap-2d \
    ros-jazzy-nav2-lifecycle-manager \
    ros-jazzy-nav2-msgs \
    ros-jazzy-launch-testing \
    ros-jazzy-launch-pytest \
 && rm -rf /var/lib/apt/lists/*
