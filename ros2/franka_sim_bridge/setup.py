from setuptools import find_packages, setup

package_name = "franka_sim_bridge"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/franka_sim_bridge.launch.py"]),
        ("share/" + package_name, ["README.md"]),
    ],
    install_requires=["setuptools", "numpy"],
    zip_safe=True,
    maintainer="R2",
    maintainer_email="r2@lab.local",
    description="FR3 CTRL-SIM Low bridge (TECH-02 ↔ Isaac official JointStates)",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "bridge_node = franka_sim_bridge.bridge_node:main",
        ],
    },
)
