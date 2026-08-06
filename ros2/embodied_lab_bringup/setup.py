from setuptools import find_packages, setup

package_name = "embodied_lab_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (
            "share/" + package_name + "/launch",
            [
                "launch/go2_bringup.launch.py",
                "launch/franka_ctrl_sim.launch.py",
            ],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="P2",
    maintainer_email="p2@lab.local",
    description="Embodied lab bringup (Go2 + FR3 CTRL-SIM)",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "run_context_node = embodied_lab_bringup.run_context_node:main",
            "safety_coordinator = embodied_lab_bringup.safety_coordinator:main",
            "limiter_node = embodied_lab_bringup.limiter_node:main",
        ],
    },
)
