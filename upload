#!/bin/bash

# Upload input file to destination specified.
# Copyright (C) 2020 Joshua Price (joshuapricew@gmail.com)
# Permission to copy and modify is granted under the MIT license
# Last revised 2021-01-20

# Destinations this script supports:
# - 0x0.st
# - x0.at
# - asgard
# - catgirlsare.sexy

# Uploader functions echo the final url of the destination and also append that to $urls

# When adding new uploaders:
# - Add flag and description to --help command.
# - Add flag to getopt and case statement
# - Copy if statement for "if destination is in array" from previous examples, modifying if statement, and function called.
# - Write uploader function to echo url and append url to $urls


# saner programming env: these switches turn some bugs into errors
set -o errexit -o pipefail -o noclobber -o nounset


# Variables - Ones that can be changed at runtime should not be readonly
CATGIRLS_KEY=''
readonly ASGARD_ROOT='/opt/media'
ASGARD_PATH='.misc'

# Uploads single input file to 0x0
0x0_upload() {
    # Upload file.
    local response
    response=$(curl --no-progress-meter --fail --retry 2 --connect-timeout 30 -speed-limit 1k -F file=@"${1}" https://0x0.st | sed 's/#nsfw//' 2>&1) || error "$?" "Failed"

    # Save and output url.
    urls+=( "${response}" )
    echo "${urls[-1]}"
}

# Uploads single input file to x0
x0_upload() {
    # Upload file.
    local response
    response=$(curl --no-progress-meter --fail --retry 2 --connect-timeout 30 -speed-limit 1k -F file=@"${1}" https://x0.at 2>&1) || error "$?" "x0: ${response}"

    # Save and output url.
    urls+=( "${response}" )
    echo "${urls[-1]}"
}

# Uploads single input file to catgirls
catgirls_upload() {
    # Upload file.
    local response
    response=$(curl --no-progress-meter --fail --retry 2 --connect-timeout 30 -speed-limit 1k -F key="${CATGIRLS_KEY}" -F file=@"${1}" https://catgirlsare.sexy/api/upload 2>&1) || error "$?" "catgirls: ${response}"

    # Save and output url.
    urls+=( "$(python3 -c "import sys, json; print(json.load(sys.stdin)['url'])" <<< "${response}" 2>/dev/null)" ) || {
        # Catgirls doesn't give curl an error response code when a key is bad.
        error 1 "$(python3 -c "import sys, json; print(json.load(sys.stdin)['error'])" <<< "${response}")"
    }
    echo "${urls[-1]}"
}

# Uploads single input file to asgard
asgard_upload() {
    # Upload file.
    if [[ -z ${SSH_ASKPASS:-} ]] && ! ssh-add -qL >/dev/null 2>&1; then
        error 0 "SSH_ASKPASS is not set, upload may fail."
    fi
    local fail_count=0
    # TODO: Doesn't seem to allow custom folders?
    until scp -qo "ServerAliveInterval 3" "${1}" "asgard.joshwprice.com:${ASGARD_ROOT}/${ASGARD_PATH}/"; do
        ((fail_count++))
        if [[ ${fail_count} = 3 ]]; then
            error 1 "Upload to asgard failed 3 times"
        fi
    done

    # Save and output url.
    # 2021-01-15 Change to commented out line if something other than spaces breaks final link.
    # urls+=( "https://asgard.kruitana.com/$(python -c 'import urllib.request, sys; print(urllib.request.pathname2url(sys.argv[1]))' "${1}")" )
    urls+=( "https://asgard.kruitana.com/${1// /%20}" )
    echo "${urls[-1]}"
}

prefix_element() {
    local e output prefix="${1}"
    shift
    for e; do 
        output+=( "${prefix}" )
        output+=( "${e}" )
    done
    echo "${output[@]}"
}

# Returns true if first parameter is in array specified as the second parameter
contains_element() {
    local e match="${1}"
    shift
    for e; do [[ ${e} = "${match}" ]] && return 0; done
    return 1
}

# Removes duplicates in input array
remove_duplicates() {
    local copy=( "$@" )
    for p; do
        for i in "${!copy[@]}"; do
            for j in "${!copy[@]}"; do
                if [[ ${copy[$i]} = "${copy[$j]}" ]] && [[ ${i} != "${j}" ]]; then
                    unset "copy[$j]"
                    break 2
                fi
            done
        done
    done
    # Output correct input for eval
    for i in "${copy[@]}"; do
        echo -n "'${i/\'/\'\\\'\'}' "
    done
}

# Replaces "-" with 1st parameter, second parameter is the array to remove from
replace_stdin_flag() {
    local copy=( "${@:2}" ) 
    for i in "${!copy[@]}"; do
        if [[ ${copy[${i}]} = "-" ]]; then
            copy[${i}]="${1}"
        fi
    done
    # Output correct input for eval
    for i in "${copy[@]}"; do
        echo -n "'${i/\'/\'\\\'\'}' "
    done
}

# Takes parameter 1 as error number and quits, does not quit if error code is 0
# All other parameters are output to stderr.
error() {
    if [[ -n ${2:-} ]]; then
        echo "${0##*/}: ${*:2}" >&2
    fi
    if [[ -n ${NOTIFY:-} ]]; then
        notify-send -a "${NOTIFY}" -i "error" "Failed${2:+: ${*:2}}"
    fi
    if [[ ${1:-1} != 0 ]]; then
        exit "${1:-1}"
    fi
}

print_help() {
    cat << EOF
Usage: ${0##*/} [OPTION]... FILE...
 Where FILE is the file to be uploaded.
 If FILE is not specified the program will fail.
 If FILE is - data is read from standard input.
 
Options:
 -c, --clipboard		copy the response url to clipboard
 -n, --notify[=APPNAME]		send a notification upon completion; APPNAME is
 				  the name to be displayed by the notification
 --0x0				upload to 0x0
 --x0				upload to x0
 --asgard[=PATH]		upload to asgard; PATH is the file upload path
 				  on asgard
 --catgirls[=KEY]		upload to catgirlsare.sexy; KEY is the API Key
 	        		  required by catgirls for uploading
 -h, --help			display this help'
EOF
}


# start parsing of options

# allow a command to fail with !’s side effect on errexit
# use return value from ${PIPESTATUS[0]}, because ! hosed $?
# shellcheck disable=SC2251
! getopt --test > /dev/null 
if [[ ${PIPESTATUS[0]} -ne 4 ]]; then
    # shellcheck disable=SC2016
    error 1 '`getopt --test` failed in this environment.'
fi

OPTIONS=hcn::
LONGOPTS=help,clipboard,notify::,0x0,x0,asgard::,catgirls::

# regarding ! and PIPESTATUS see above
# temporarily store output to be able to check for errors
# activate quoting/enhanced mode (e.g. by writing out “--options”)
# pass arguments only via   -- "$@"   to separate them correctly
# shellcheck disable=SC2016
! PARSED=$(getopt --options="$OPTIONS" --longoptions="$LONGOPTS" --name "${0##*/}" -- "$@")
if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    # e.g. return value is 1
    #  then getopt has complained about wrong arguments to stderr
    exit 2
fi
# read getopt’s output this way to handle the quoting right:
eval set -- "$PARSED"

# now enjoy the options in order and nicely split until we see --
while true; do
    case "$1" in
        -h|--help)
            print_help  
            exit 0
            ;;

        -n|--notify)
            # If notify-send is not installed, quit.
            hash notify-send 2>/dev/null || {
                # shellcheck disable=SC2016
                error 1 '`notify-send` not found.'
            }
            # If there is not a notification server, quit.
            if ! busctl --user list --acquired | grep org.freedesktop.Notifications >/dev/null; then
                error 1 "No available notification server"
            fi
            # TODO: Add check before actually running clipboard

            readonly NOTIFY="${2:-"${0##*/}"}"
            shift 2
            ;;

        -c|--clipboard)
            # If xclip is not installed, quit.
            hash xclip 2>/dev/null || { 
            # shellcheck disable=SC2016
                error 1 '`xclip` not found'
            }
            # TODO: Add check before actually running xclip

            # Fixes multiple --clipboards counting as more than one service, required to test if clipboard is the only service passed
            if ! contains_element "clipboard" "${destinations[@]}"; then
                destinations+=(clipboard)
            fi
            shift
            ;;
	
        --0x0)
            destinations+=(0x0)
            shift
            ;;

        --x0)
            destinations+=(x0)
            shift
            ;;

        --asgard)
            # Test if optional path is set, prioritising option passed in
            if [[ -n ${2} ]]; then
                ASGARD_PATH="${2}"
            fi
            if [[ -z ${ASGARD_PATH:-} ]]; then
                error 1 "No path set for asgard"
            fi

            destinations+=(asgard)
            shift 2
            ;;

        --catgirls)
            # Test if optional key is set, prioritising option passed in
            if [[ -n ${2} ]]; then
                CATGIRLS_KEY="${2}"
            fi
            if [[ -z ${CATGIRLS_KEY:-} ]]; then
                error 1 "No key set for catgirls"
            fi

            destinations+=(catgirls)
            shift 2
            ;;

        --)
            readonly ASGARD_PATH
            readonly CATGIRLS_KEY

            readonly destinations
            shift
            break
            ;;

        *)
            error 101 "Programming error"
            ;;
    esac
done


# Remove repeats of the same file
eval set -- "$(remove_duplicates "$@")"

# If requested, get file from stdin
if contains_element "-" "$@"; then
    set +o noclobber
    stdin_file="$(mktemp)"
    cat > "${stdin_file}"
    set -o noclobber
    eval set -- "$(replace_stdin_flag "${stdin_file}" "$@")"
fi

# check files exist
for file in "$@"; do
    if ! [[ -f ${file} ]]; then
        error 10 "File '${file}' does not exist"
    fi
done

# handle non-option arguments
if [[ $# -lt 1 ]]; then
        error 4 "At least a single input file is required"
fi

# Ensure one destination is specified
if [[ -z ${destinations:-} ]]; then
    error 1 "At least one destination must be specified"
fi

# If --x0 flag was passed, upload files to x0
if contains_element "x0" "${destinations[@]}"; then
    for file in "$@"; do
        x0_upload "${file}"
    done
fi

# If --0x0 flag was passed, upload files to x0
if contains_element "0x0" "${destinations[@]}"; then
    for file in "$@"; do
        0x0_upload "${file}"
    done
fi

# If --asgard flag was passed, upload files to asgard
if contains_element "asgard" "${destinations[@]}"; then
    for file in "$@"; do
        asgard_upload "${file}"
    done
fi

# If --catgirls flag was passed, upload files to catgirls
if contains_element "catgirls" "${destinations[@]}"; then
    for file in "$@"; do
        catgirls_upload "${file}"
    done
fi



# Calculate this now, could be used in later functions
mime_type="$(file --brief --mime-type "${1}")"

# If the --clipboard flag was passed, copy the url to clipboard, or if only --clipboard was passed, copy file directly to clipboard
if contains_element "clipboard" "${destinations[@]}"; then
    if [[ ${#destinations[@]} -eq 1 ]]; then
        if [[ $# -eq 1 ]]; then
            xclip -selection clipboard -t "${mime_type}" < "${1}"
            urls+=( "${1}" )
        else
            error 1 "Single input file required for setting destination to clipboard"
        fi
    else
        for url in "${urls[@]}"; do
            echo "${url}"
        done | xclip -selection clipboard -r
    fi
fi


# If the --notify flag was passed, send a notification
if [[ -n ${NOTIFY:-} ]]; then
    # Multiple filenames should not be put in the notification
    if [[ ${#urls[@]} -eq 1 ]]; then
        # If it's an image, show it in the notification!
        filetype="$(cut -f1 -d'/' <<< "${mime_type}")"
        if [[ ${filetype} = "image" ]]; then
            # Save to a file because notify-send acts weird without normal files and absolute paths
            convert -adaptive-resize 256 "${1}" "${icon_file:=$(mktemp)}"
            notify-send -u low -a "${NOTIFY}" -i "${icon_file}" "Image \"${urls[0]##*/}\" uploaded"
            rm "${icon_file}"
        else
            notify-send -u low -a "${NOTIFY}" -i "${filetype}" "File \"${urls[0]##*/}\" uploaded"
        fi
    else
        notify-send -u low -a "${NOTIFY}" -i "folder" "Files uploaded"
    fi
fi

if [[ -n ${stdin_file:-} ]]; then
    rm "${stdin_file}"
fi

# TODO: Add trap cleanup function
# vim: shiftwidth=4 expandtab autoindent
