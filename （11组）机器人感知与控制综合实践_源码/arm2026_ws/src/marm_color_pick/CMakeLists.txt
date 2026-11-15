cmake_minimum_required(VERSION 3.0.2)
project(marm_color_pick)
find_package(catkin REQUIRED)
catkin_package()
catkin_install_python(PROGRAMS scripts/color_pick_node.py scripts/test_color_pick.py scripts/validate_runtime.py scripts/gesture_bridge.py scripts/perception_node.py scripts/windows_camera.py scripts/benchmark_perception.py scripts/check_course_system.py scripts/test_motion_runtime.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(FILES scripts/pick_core.py scripts/perception_core.py DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
install(DIRECTORY launch config DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION})
install(DIRECTORY gesture_pc DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  PATTERN "__pycache__" EXCLUDE)
