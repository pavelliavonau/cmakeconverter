include("${CMAKE_CURRENT_LIST_DIR}/Default.cmake")

get_target_property(${PROPS_TARGET}_BINARY_DIR ${PROPS_TARGET} BINARY_DIR)
set_target_properties(${PROPS_TARGET} PROPERTIES Fortran_MODULE_DIRECTORY "${${PROPS_TARGET}_BINARY_DIR}/Modules.dir")
