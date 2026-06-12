from setuptools import find_packages, setup

package_name = "go2_driver_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/go2_bridge.launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="P2",
    maintainer_email="p2@lab.local",
    description="Unitree Go2 driver bridge",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "bridge_node = go2_driver_bridge.bridge_node:main",
        ],
    },
)
