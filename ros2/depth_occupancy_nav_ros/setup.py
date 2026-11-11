# SPDX-License-Identifier: Apache-2.0
from setuptools import find_packages, setup
import os
from glob import glob

package_name = "depth_occupancy_nav_ros"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Arpan Bom",
    maintainer_email="applycoding@gmail.com",
    description="Synthetic depth to OccupancyGrid ROS 2 node (simulation only).",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "depth_occupancy_node = depth_occupancy_nav_ros.node:main",
            "locked_scene_publisher = depth_occupancy_nav_ros.locked_scene_publisher:main",
        ],
    },
)
