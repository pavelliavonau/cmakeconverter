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
# Input:
#    Options:
#       PRE_BUILD  - Pre build event
#       PRE_LINK   - Pre link event
#       POST_BUILD - Post build event
#
#    One value args:
#       TARGET - Target
#       OUTPUT - Output files
#
#    Lists:
#       DEPENDS  - Files on which the command depends
#       COMMANDS - List of commands(COMMAND condition1 commannd1 args1 COMMAND condition2 commannd2 args2 ...)
# Output:
#    OUTPUT     - Output files
#    DEPENDS    - Files on which the command depends
#    COMMENT    - Comment
#    PRE_BUILD  - TRUE/FALSE
#    PRE_LINK   - TRUE/FALSE
#    POST_BUILD - TRUE/FALSE
#    TARGET     - Target name
#    COMMANDS   - Prepared commands(every token is wrapped in CONDITION)
#    NAME       - Unique name for custom target
#    STEP       - PRE_BUILD/PRE_LINK/POST_BUILD
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
# There are two main signatures for add_custom_command_if.
#
# Generating Files
# The first signature is for adding a custom command to produce an output:
#     add_custom_command_if(
#         OUTPUT output1 [output2 ...]
#         COMMANDS
#         COMMAND condition command1 [args1...]
#         [COMMAND condition command2 [args2...]]
#         [DEPENDS [depends...]]
#         [COMMENT comment]
#
# Build Events
#     add_custom_command_if(
#         TARGET target
#         PRE_BUILD | PRE_LINK | POST_BUILD
#         COMMAND condition command1 [args1...]
#         [COMMAND condition command2 [args2...]]
#         [COMMENT comment]
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
# Add link directory
#     target_link_directories(<target> [[CONDITION condition] [item1 [item2 [...]]]]...)
################################################################################
cmake_policy(PUSH)
cmake_policy(SET CMP0054 NEW)
function(target_link_directories TARGET)
    if(${CMAKE_GENERATOR} MATCHES "Visual Studio")
        set(QUOTE "")
    else()
        set(QUOTE "\"")
    endif()

    unset(LINK_DIRS)
    unset(ARG_ROLE)
    set(CONDITION "1")
    foreach(ARG ${ARGN})
        if("${ARG}" STREQUAL "CONDITION")
            set(ARG_ROLE "CONDITION_KEYWORD")
        elseif("${ARG_ROLE}" STREQUAL "CONDITION_KEYWORD")
            set(ARG_ROLE "CONDITION")
        else()
            set(ARG_ROLE "PATH")
        endif()

        if("${ARG_ROLE}" STREQUAL "CONDITION")
            set(CONDITION "${ARG}")
        elseif("${ARG_ROLE}" STREQUAL "PATH")
            list(APPEND LINK_DIRS "$<${CONDITION}:${CMAKE_LIBRARY_PATH_FLAG}${QUOTE}${ARG}${QUOTE}>")
        endif()
    endforeach()

    target_link_libraries(${TARGET} ${LINK_DIRS})
endfunction()
cmake_policy(POP)
