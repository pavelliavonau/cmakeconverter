# utils file for projects came from visual studio solution with cmake-converter.

################################################################################
# Wrap each token of the command with condition
################################################################################
cmake_policy(PUSH)
cmake_policy(SET CMP0054 NEW)
macro(prepare_commands)
    unset(TOKEN_ROLE)
    unset(COMMANDS)
    foreach(TOKEN ${ARG_COMMANDS})
        if("${TOKEN}" STREQUAL "COMMAND")
            set(TOKEN_ROLE "KEYWORD")
        elseif("${TOKEN_ROLE}" STREQUAL "KEYWORD")
            set(TOKEN_ROLE "CONDITION")
        elseif("${TOKEN_ROLE}" STREQUAL "CONDITION")
            set(TOKEN_ROLE "COMMAND")
        elseif("${TOKEN_ROLE}" STREQUAL "COMMAND")
            set(TOKEN_ROLE "ARG")
        endif()

        if("${TOKEN_ROLE}" STREQUAL "KEYWORD")
            list(APPEND COMMANDS "${TOKEN}")
        elseif("${TOKEN_ROLE}" STREQUAL "CONDITION")
            set(CONDITION ${TOKEN})
        elseif("${TOKEN_ROLE}" STREQUAL "COMMAND")
            list(APPEND COMMANDS "$<$<NOT:${CONDITION}>:${DUMMY}>$<${CONDITION}:${TOKEN}>")
        elseif("${TOKEN_ROLE}" STREQUAL "ARG")
            list(APPEND COMMANDS "$<${CONDITION}:${TOKEN}>")
        endif()
    endforeach()
endmacro()
cmake_policy(POP)

################################################################################
# Transform all the tokens to absolute paths
################################################################################
macro(prepare_output)
    unset(OUTPUT)
    foreach(TOKEN ${ARG_OUTPUT})
        if(IS_ABSOLUTE ${TOKEN})
            list(APPEND OUTPUT "${TOKEN}")
        else()
            list(APPEND OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/${TOKEN}")
        endif()
    endforeach()
endmacro()

################################################################################
# Parse add_custom_command_if args.
#
# Input:
#     PRE_BUILD  - Pre build event option
#     PRE_LINK   - Pre link event option
#     POST_BUILD - Post build event option
#     TARGET     - Target
#     OUTPUT     - List of output files
#     DEPENDS    - List of files on which the command depends
#     COMMANDS   - List of commands(COMMAND condition1 commannd1 args1 COMMAND
#                  condition2 commannd2 args2 ...)
# Output:
#     OUTPUT     - Output files
#     DEPENDS    - Files on which the command depends
#     COMMENT    - Comment
#     PRE_BUILD  - TRUE/FALSE
#     PRE_LINK   - TRUE/FALSE
#     POST_BUILD - TRUE/FALSE
#     TARGET     - Target name
#     COMMANDS   - Prepared commands(every token is wrapped in CONDITION)
#     NAME       - Unique name for custom target
#     STEP       - PRE_BUILD/PRE_LINK/POST_BUILD
################################################################################
function(add_custom_command_if_parse_arguments)
    cmake_parse_arguments("ARG" "PRE_BUILD;PRE_LINK;POST_BUILD" "TARGET;COMMENT" "DEPENDS;OUTPUT;COMMANDS" ${ARGN})

    if(WIN32)
        set(DUMMY "cd.")
    elseif(UNIX)
        set(DUMMY "true")
    endif()

    prepare_commands()
    prepare_output()

    set(DEPENDS "${ARG_DEPENDS}")
    set(COMMENT "${ARG_COMMENT}")
    set(PRE_BUILD "${ARG_PRE_BUILD}")
    set(PRE_LINK "${ARG_PRE_LINK}")
    set(POST_BUILD "${ARG_POST_BUILD}")
    set(TARGET "${ARG_TARGET}")
    if(PRE_BUILD)
        set(STEP "PRE_BUILD")
    elseif(PRE_LINK)
        set(STEP "PRE_LINK")
    elseif(POST_BUILD)
        set(STEP "POST_BUILD")
    endif()
    set(NAME "${TARGET}_${STEP}")

    set(OUTPUT "${OUTPUT}" PARENT_SCOPE)
    set(DEPENDS "${DEPENDS}" PARENT_SCOPE)
    set(COMMENT "${COMMENT}" PARENT_SCOPE)
    set(PRE_BUILD "${PRE_BUILD}" PARENT_SCOPE)
    set(PRE_LINK "${PRE_LINK}" PARENT_SCOPE)
    set(POST_BUILD "${POST_BUILD}" PARENT_SCOPE)
    set(TARGET "${TARGET}" PARENT_SCOPE)
    set(COMMANDS "${COMMANDS}" PARENT_SCOPE)
    set(STEP "${STEP}" PARENT_SCOPE)
    set(NAME "${NAME}" PARENT_SCOPE)
endfunction()

################################################################################
# Add conditional custom command
#
# Generating Files
# The first signature is for adding a custom command to produce an output:
#     add_custom_command_if(
#         <OUTPUT output1 [output2 ...]>
#         <COMMANDS>
#         <COMMAND condition command1 [args1...]>
#         [COMMAND condition command2 [args2...]]
#         [DEPENDS [depends...]]
#         [COMMENT comment]
#
# Build Events
#     add_custom_command_if(
#         <TARGET target>
#         <PRE_BUILD | PRE_LINK | POST_BUILD>
#         <COMMAND condition command1 [args1...]>
#         [COMMAND condition command2 [args2...]]
#         [COMMENT comment]
#
# Input:
#     output     - Output files the command is expected to produce
#     condition  - Generator expression for wrapping the command
#     command    - Command-line(s) to execute at build time.
#     args       - Command`s args
#     depends    - Files on which the command depends
#     comment    - Display the given message before the commands are executed at
#                  build time.
#     PRE_BUILD  - Run before any other rules are executed within the target
#     PRE_LINK   - Run after sources have been compiled but before linking the
#                  binary
#     POST_BUILD - Run after all other rules within the target have been
#                  executed
################################################################################
function(add_custom_command_if)
    add_custom_command_if_parse_arguments(${ARGN})

    if(OUTPUT AND TARGET)
        message(FATAL_ERROR  "Wrong syntax. A TARGET and OUTPUT can not both be specified.")
    endif()

    if(OUTPUT)
        add_custom_command(OUTPUT ${OUTPUT}
                           ${COMMANDS}
                           DEPENDS ${DEPENDS}
                           WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                           COMMENT ${COMMENT})
    elseif(TARGET)
        if(PRE_BUILD AND NOT ${CMAKE_GENERATOR} MATCHES "Visual Studio")
            add_custom_target(
                ${NAME}
                ${COMMANDS}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                COMMENT ${COMMENT})
            add_dependencies(${TARGET} ${NAME})
        else()
            add_custom_command(
                TARGET ${TARGET}
                ${STEP}
                ${COMMANDS}
                WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
                COMMENT ${COMMENT})
        endif()
    else()
        message(FATAL_ERROR "Wrong syntax. A TARGET or OUTPUT must be specified.")
    endif()
endfunction()

################################################################################
# Use props file for a target and configs
#     use_props(<target> <configs...> <props_file>)
# Inside <props_file> there are following variables:
#     PROPS_TARGET   - <target>
#     PROPS_CONFIG   - One of <configs...>
#     PROPS_CONFIG_U - Uppercase PROPS_CONFIG
# Input:
#     target      - Target to apply props file
#     configs     - Build configurations to apply props file
#     props_file  - CMake script
################################################################################
macro(use_props TARGET CONFIGS PROPS_FILE)
    set(PROPS_TARGET "${TARGET}")
    foreach(PROPS_CONFIG ${CONFIGS})
        string(TOUPPER "${PROPS_CONFIG}" PROPS_CONFIG_U)

        get_filename_component(ABSOLUTE_PROPS_FILE "${PROPS_FILE}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_LIST_DIR}")
        if(EXISTS "${ABSOLUTE_PROPS_FILE}")
            include("${ABSOLUTE_PROPS_FILE}")
        else()
            message(WARNING "Corresponding cmake file from props \"${ABSOLUTE_PROPS_FILE}\" doesn't exist")
        endif()
    endforeach()
endmacro()

################################################################################
# Add compile options to source file
#     source_file_compile_options(<source_file> [compile_options...])
# Input:
#     source_file     - Source file
#     compile_options - Options to add to COMPILE_FLAGS property
################################################################################
function(source_file_compile_options SOURCE_FILE)
    if("${ARGC}" LESS_EQUAL "1")
        return()
    endif()

    get_source_file_property(COMPILE_OPTIONS "${SOURCE_FILE}" COMPILE_OPTIONS)

    if(COMPILE_OPTIONS)
        list(APPEND COMPILE_OPTIONS ${ARGN})
    else()
        set(COMPILE_OPTIONS "${ARGN}")
    endif()

    set_source_files_properties("${SOURCE_FILE}" PROPERTIES COMPILE_OPTIONS "${COMPILE_OPTIONS}")
endfunction()

################################################################################
# Create precompiled header for a list of source files
#     use_precompiled_header(<src_list_var> <header_file> <source_file>)
# Input:
#     src_list_var - Name of source file list variable
#     header_file  - Precompiled header file
#     source_file  - Source file to precompile
################################################################################
function(use_precompiled_header SRC_LIST_VAR HEADER_FILE SOURCE_FILE)
    if(NOT MSVC)
        target_precompile_headers(${PROJECT_NAME} PRIVATE
            "$<$<COMPILE_LANGUAGE:CXX>:${CMAKE_CURRENT_SOURCE_DIR}/${HEADER_FILE}>")
        return()
    endif()

    get_filename_component(PCH_HEADER ${HEADER_FILE} NAME)
    get_filename_component(PCH_BINARY ${HEADER_FILE} NAME_WE)

    set(PCH_BINARY "${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR}/${PCH_BINARY}.pch")
    set(HEADER_COPY "${CMAKE_CURRENT_BINARY_DIR}/${CMAKE_CFG_INTDIR}/${HEADER_FILE}")
    add_custom_command(OUTPUT ${HEADER_COPY}
        COMMAND ${CMAKE_COMMAND} -E copy
                ${CMAKE_CURRENT_SOURCE_DIR}/${HEADER_FILE} ${HEADER_COPY}
        DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${HEADER_FILE})

    set_source_files_properties(${HEADER_COPY} PROPERTIES GENERATED "TRUE")
    add_custom_target(${PROJECT_NAME}_PCH DEPENDS ${HEADER_COPY})
    add_dependencies(${PROJECT_NAME} ${PROJECT_NAME}_PCH)

    set(SRC_LIST ${${SRC_LIST_VAR}})
    list(FILTER SRC_LIST INCLUDE REGEX ".*\.cpp")
    list(FILTER SRC_LIST EXCLUDE REGEX "${SOURCE_FILE}")

    set_source_files_properties(${SRC_LIST} PROPERTIES
        COMPILE_FLAGS "/Yu${PCH_HEADER} /Fp\"${PCH_BINARY}\""
        OBJECT_DEPENDS "${PCH_BINARY}")

    set_source_files_properties(${SOURCE_FILE} PROPERTIES
        COMPILE_FLAGS "/Yc${PCH_HEADER} /Fp\"${PCH_BINARY}\""
        OBJECT_OUTPUTS "${PCH_BINARY}"
        OBJECT_DEPENDS "")
endfunction()

################################################################################
# Default properties of visual studio projects
################################################################################
set(DEFAULT_CXX_PROPS "${CMAKE_CURRENT_LIST_DIR}/DefaultCXX.cmake")
set(DEFAULT_Fortran_PROPS "${CMAKE_CURRENT_LIST_DIR}/DefaultFortran.cmake")
