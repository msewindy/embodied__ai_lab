cmake_minimum_required(VERSION 3.8)
project(embodied_lab_msgs)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

set(msg_files
  msg/RunContext.msg
  msg/NodeHealth.msg
  msg/RobotState.msg
  msg/SkillIntent.msg
  msg/TeleopCommand.msg
  msg/JointCommand.msg
  msg/SafetyState.msg
)

set(srv_files
  srv/BridgeSmoke.srv
  srv/GetRunContext.srv
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  ${srv_files}
  DEPENDENCIES std_msgs geometry_msgs builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
