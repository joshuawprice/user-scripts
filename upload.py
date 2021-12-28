#!/usr/bin/env python3

from abc import ABC, abstractmethod
import argparse
import os
from typing import BinaryIO
import requests
import sys
import subprocess
import urllib.request


# Code from before using intermixed parsing.
################################################################
# Dedupe input files based on absolute file path
# class files(argparse.Action):
#     def __call__(self, parser, namespace, values, option_string=None):
#         # Remove duplicates
#         for i in range(0, len(values)):
#             for j in range(i + 1, len(values)):
#                 if (os.path.abspath(values[i].name) ==
#  os.path.abspath(values[j].name)):
#                     values.pop(j)

#         # Append extra files found
#         for i in extra_files:
#             values.append(i)

#         setattr(namespace, self.dest, values)


# class destinations_with_optional_value(argparse.Action):
#     def __call__(self, parser, namespace, value, option_string=None):
#         if not value.endswith("/"):
#             if os.path.isfile(value):
#                 if getattr(namespace, "files") != None:
#                     print(
#                         f"Local file given to {option_string} flag. Dazed
#  and confused, but trying to continue", file=sys.stderr)
#                 else:
#                     extra_files.append(open(value, 'rb'))
#                     value = self.const
#         else:
#             value = value.rstrip("/")

#         setattr(namespace, self.dest, value)
################################################################


class Uploader(ABC):
    @abstractmethod
    def upload(self, file: BinaryIO) -> None:
        raise NotImplementedError


class TheNullPointer(Uploader):
    def upload(self, file: BinaryIO) -> None:
        r = requests.post("https://0x0.st", files={"file": file})
        r.raise_for_status()
        print(r.text.strip())


class X0(Uploader):
    def upload(self, file: BinaryIO) -> None:
        r = requests.post("https://x0.at", files={"file": file})
        r.raise_for_status()
        print(r.text.strip())


class Catgirls(Uploader):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def upload(self, file: BinaryIO) -> None:
        r = requests.post(
            "https://catgirlsare.sexy/api/upload",
            data={"key": self.api_key},
            files={"file": file})
        r.raise_for_status()
        print(r.json()["url"])


class Asgard(Uploader):
    def __init__(self, location: str) -> None:
        self.location = location

        # TODO: Look up ssh agents to check if SSH_ASKPASS is really required.
        if (not os.getenv("SSH_ASKPASS")
            and bool(subprocess.run([
                "ssh-add", "-qL"],
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                .returncode)):
            print("SSH_ASKPASS is not set, upload to asgard may fail.",
                  file=sys.stderr)

    def upload(self, file: BinaryIO) -> None:
        for i in range(3):
            if not bool(
                    subprocess.run([
                        "scp",
                        "-qo",
                        "ServerAliveInterval 3",
                        file.name,
                        f"asgard.joshwprice.com:/opt/media/{self.location}/"])
                    .returncode):
                break
        else:
            print("Upload to asgard failed 3 times.")
            sys.exit(1)
        print("https://files.kruitana.com/"
              + urllib.request.pathname2url(file.name))


def the_null_pointer_upload(files: list[BinaryIO]) -> None:
    for file in files:
        r = requests.post("https://0x0.st", files={"file": file})
        r.raise_for_status()
        print(r.text.strip())
        file.seek(0)


def x0_upload(files: list[BinaryIO]) -> None:
    for file in files:
        r = requests.post("https://x0.at", files={"file": file})
        r.raise_for_status()
        print(r.text.strip())
        file.seek(0)


def catgirls_upload(files: list[BinaryIO], api_key: str) -> None:
    for file in files:
        r = requests.post(
            "https://catgirlsare.sexy/api/upload",
            data={"key": api_key},
            files={"file": file})
        r.raise_for_status()
        print(r.json()["url"])
        file.seek(0)


def asgard_upload(files: list[BinaryIO], location: str):
    if (not os.environ["SSH_ASKPASS"]
            and bool(subprocess.run([
                "ssh-add", "-qL"],
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                    .returncode)):
        print("SSH_ASKPASS is not set, upload may fail.", file=sys.stderr)

    for file in files:
        for i in range(3):
            if not bool(subprocess.run([
                    "scp",
                    "-qo",
                    "ServerAliveInterval 3",
                    file.name,
                    f"asgard.joshwprice.com:/opt/media/{location}/"])
                        .returncode):
                break
        else:
            print("Upload to asgard failed 3 times.")
            sys.exit(1)
        file.seek(0)


def at_least_one_dest(args: type[argparse.Namespace]) -> bool:
    for destination in destinations:
        if getattr(args, destination):
            return True
    return False


def main():
    # Start parsing options
    parser = argparse.ArgumentParser(
        description="Uploads file to destination specified.")
    # Miscellaneous features
    parser.add_argument("-n", "--notify", action="store_true",
                        help="send a notification upon completion")
    parser.add_argument("-c", "--clipboard", action="store_true",
                        help="copy the response url to clipboard")

    # Add destinations for the script
    destinations_group = parser.add_argument_group(
        "destinations",
        """care should be taken when using arguments with optional values as
        if it is given a valid file on your filesystem, it will ignore it""")
    destinations_group.add_argument(
        "--0x0", action="store_true", help="upload to 0x0.st")
    destinations_group.add_argument(
        "--x0", action="store_true", help="upload to x0.at")
    destinations_group.add_argument(
        "--asgard", nargs='?',
        const=".misc",  help="upload to asgard")
    destinations_group.add_argument(
        "--catgirls", nargs='?',
        const="",
        help="upload to catgirlsare.sexy")
    # destinations_group.add_argument(
    #     "-c", "--clipboard", action="store_true",
    #     help="only allowed if this is the only destination;"
    #          "saves file to clipboard")

    # Finally, allow files to be uploaded, including - (stdin)
    # TODO: Maybe remove dupes? see files action class for how.
    parser.add_argument(
        "files", type=argparse.FileType('rb'),
        metavar="FILE", nargs="+", help="file to be uploaded")

    # Save parsed arguments to args object
    args = parser.parse_intermixed_args()

    # Debugging
    print(args.files, file=sys.stderr)
    print(args, file=sys.stderr)

    # Quit if no destinations are given
    # TODO: If catgirls is empty then give better error message.
    if not at_least_one_dest(args):
        parser.error("at least one destination is required")

    if getattr(args, "0x0"):
        the_null_pointer_upload(args.files)

    if args.x0:
        x0_upload(args.files)

    if args.catgirls:
        catgirls_upload(args.files, args.catgirls)

    if args.asgard:
        asgard_upload(args.files, args.asgard)

    # Reminder: Make uploader classes!


if __name__ == "__main__":
    # TODO: Add clipboard uploader
    destinations = ["0x0", "x0", "asgard", "catgirls"]
    main()

# vim: shiftwidth=4 expandtab autoindent
