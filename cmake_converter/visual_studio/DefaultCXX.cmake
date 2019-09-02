include("${CMAKE_CURRENT_LIST_DIR}/Default.cmake")

if(MSVC)
    create_property_reader("DEFAULT_CXX_DEBUG_RUNTIME_LIBRARY")
    create_property_reader("DEFAULT_CXX_RUNTIME_LIBRARY")
    create_property_reader("DEFAULT_CXX_EXCEPTION_HANDLING")
    create_property_reader("DEFAULT_CXX_DEBUG_INFORMATION_FORMAT")

    set_config_specific_property("DEFAULT_CXX_DEBUG_RUNTIME_LIBRARY" "/MDd")
    set_config_specific_property("DEFAULT_CXX_RUNTIME_LIBRARY" "/MD")
    set_config_specific_property("DEFAULT_CXX_EXCEPTION_HANDLING" "/EHsc")
    set_config_specific_property("DEFAULT_CXX_DEBUG_INFORMATION_FORMAT" "/Zi")
endif()
