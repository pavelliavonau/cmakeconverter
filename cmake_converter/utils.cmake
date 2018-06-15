# utils file for projects came from visual studio solution with cmake-converter.

################################################################################
# Parse add_custom_command_if args.
# Input:
#    Options:        PRE_BUILD, PRE_LINK, POST_BUILD
#    One value args: TARGET
#    List:           List of commands(COMMAND condition1 commannd1 args1 COMMAND condition2 commannd2 args2 ...)
# Output:
#    PRE_BUILD  - TRUE/FALSE
#    PRE_LINK   - TRUE/FALSE
#    POST_BUILD - TRUE/FALSE
#    TARGET     - Target name
#    COMMANDS   - Prepared commands(every token is wrapped in CONDITION)
#    NAME       - Unique name for custom target
#    STEP       - PRE_BUILD/PRE_LINK/POST_BUILD
################################################################################
cmake_policy(PUSH)
cmake_policy(SET CMP0054 NEW)
function(add_custom_command_if_parse_arguments)
    cmake_parse_arguments("ARG" "PRE_BUILD;PRE_LINK;POST_BUILD" "TARGET" "" ${ARGN})

    unset(COMMANDS)
    foreach(TOKEN ${ARG_UNPARSED_ARGUMENTS})
        if("${TOKEN}" STREQUAL "COMMAND")
            set(TOKEN_ROLE "KEYWORD")
        elseif("${TOKEN_ROLE}" STREQUAL "KEYWORD")
            set(TOKEN_ROLE "CONDITION")
        elseif("${TOKEN_ROLE}" STREQUAL "CONDITION")
            set(TOKEN_ROLE "COMMAND")
        elseif("${TOKEN_ROLE}" STREQUAL "COMMAND")
            set(TOKEN_ROLE "COMMAND")
        endif()

        if("${TOKEN_ROLE}" STREQUAL "KEYWORD")
            set(COMMANDS ${COMMANDS} ${TOKEN})
        elseif("${TOKEN_ROLE}" STREQUAL "CONDITION")
            set(CONDITION ${TOKEN})
        elseif("${TOKEN_ROLE}" STREQUAL "COMMAND")
            set(COMMANDS ${COMMANDS} $<${CONDITION}:${TOKEN}>)
        endif()
    endforeach()

    set(PRE_BUILD "${ARG_PRE_BUILD}" PARENT_SCOPE)
    set(PRE_LINK "${ARG_PRE_LINK}" PARENT_SCOPE)
    set(POST_BUILD "${ARG_POST_BUILD}" PARENT_SCOPE)
    set(TARGET "${ARG_TARGET}" PARENT_SCOPE)
    set(COMMANDS "${COMMANDS}" PARENT_SCOPE)

    set(NAME "${TARGET}_${STEP}" PARENT_SCOPE)
    if(PRE_BUILD)
        set(STEP "PRE_BUILD" PARENT_SCOPE)
    elseif(PRE_LINK)
        set(STEP "PRE_LINK" PARENT_SCOPE)
    elseif(POST_BUILD)
        set(STEP "POST_BUILD" PARENT_SCOPE)
    endif()
endfunction()
cmake_policy(POP)

################################################################################
# Add custom command if condition is TRUE
# add_custom_command_if(
#     TARGET target
#     PRE_BUILD | PRE_LINK | POST_BUILD
#     COMMAND condition command1 [args1...]
#     [COMMAND condition command2 [args2...]]
################################################################################
function(add_custom_command_if)
    add_custom_command_if_parse_arguments(${ARGN})

    if(PRE_BUILD AND NOT ${CMAKE_GENERATOR} MATCHES "Visual Studio")
        add_custom_target(
            ${NAME}
            ${COMMANDS}
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
        add_dependencies(${TARGET} ${NAME})
    else()
        add_custom_command(
            TARGET ${TARGET}
            ${STEP}
            ${COMMANDS}
            WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
    endif()
endfunction()
