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


class SingleAppendAction(argparse.Action):
    """
    A custom action similar to the default append action. However, only
    appends one instance of a data type to dest.

    Intended to be used for ensuring uploaders are only added to dest
    once.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        # If destinations is empty, add values and return
        if not getattr(namespace, self.dest):
            setattr(namespace, self.dest, [values])
            return

        # Exit if Uploader is already in destinations
        if any((isinstance(x, type(values))
                for x in getattr(namespace, self.dest))):
            return

        # Append values to destination then resave destinations
        destinations = getattr(namespace, self.dest)
        destinations.append(values)
        setattr(namespace, self.dest, destinations)


class Uploader(ABC):
    @abstractmethod
    def upload(self, file: BinaryIO) -> None:
        raise NotImplementedError


class TheNullPointer(Uploader):
    def upload(self, file: BinaryIO) -> None:
        r = requests.post("https://0x0.st", files={"file": file}, timeout=5)
        r.raise_for_status()
        print(r.text.strip())


class X0(Uploader):
    def upload(self, file: BinaryIO) -> None:
        r = requests.post("https://x0.at", files={"file": file}, timeout=5)
        r.raise_for_status()
        print(r.text.strip())


class Catgirls(Uploader):
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError
        self.api_key = api_key

    def upload(self, file: BinaryIO) -> None:
        r = requests.post(
            "https://catgirlsare.sexy/api/upload",
            data={"key": self.api_key},
            files={"file": file},
            timeout=5)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            raise requests.exceptions.HTTPError(r.json()["error"]) from None
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
        "--0x0", action="store_const", const=TheNullPointer(),
        help="upload to 0x0.st")
    destinations_group.add_argument(
        "--x0", action="store_const", const=X0(),
        help="upload to x0.at")
    destinations_group.add_argument(
        "--asgard", nargs='?',
        const=".misc", type=Asgard,
        help="upload to asgard")
    destinations_group.add_argument(
        "--catgirls", nargs='?',
        const="", type=Catgirls,
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

    # TODO: Add clipboard uploader
    destinations = [getattr(args, x) for x in vars(args)
                    if isinstance(getattr(args, x), Uploader)]

    # Quit if no destinations are given
    if not destinations:
        parser.error("at least one destination is required")

    for destination in destinations:
        for file in args.files:
            destination.upload(file)
            file.seek(0)


if __name__ == "__main__":
    main()

# vim: shiftwidth=4 expandtab autoindent
