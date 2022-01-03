#!/usr/bin/env python3

from abc import ABC, abstractmethod
import argparse
import os
from typing import BinaryIO
import requests
import sys
import subprocess
import urllib.request


class FilesAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # Remove duplicates based on file path
        files = []
        for value in values:
            for file in files:
                if value.name == file.name:
                    value.close()
                    break
            else:
                files.append(value)

        setattr(namespace, self.dest, files)


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


class SingleAppendConstAction(SingleAppendAction):
    """
    A custom action similar to the default append const action. However,
    only appends one instance of a data type to dest.

    Intended to be used for ensuring uploaders are only added to dest
    once.
    """

    def __init__(self, option_strings, dest, const,
                 default=None, required=False, help=None, metavar=None):
        super().__init__(option_strings=option_strings, dest=dest,
                         nargs=0, const=const,
                         default=default, required=required,
                         help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        super().__call__(parser, namespace,
                         self.const, option_string)


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
        "--0x0", action=SingleAppendConstAction, const=TheNullPointer(),
        dest="destinations", help="upload to 0x0.st")
    destinations_group.add_argument(
        "--x0", action=SingleAppendConstAction, const=X0(),
        dest="destinations", help="upload to x0.at")
    destinations_group.add_argument(
        "--asgard", action=SingleAppendAction, nargs='?',
        const=".misc", type=Asgard,
        dest="destinations", help="upload to asgard")
    destinations_group.add_argument(
        "--catgirls", action=SingleAppendAction, nargs='?',
        const="", type=Catgirls,
        dest="destinations", help="upload to catgirlsare.sexy")
    # destinations_group.add_argument(
    #     "-c", "--clipboard", action="store_true",
    #     help="only allowed if this is the only destination;"
    #          "saves file to clipboard")

    # Finally, allow files to be uploaded, including - (stdin)
    parser.add_argument(
        "files", type=argparse.FileType('rb'), action=FilesAction,
        metavar="FILE", nargs="+", help="file to be uploaded")

    # Save parsed arguments to args object
    args = parser.parse_intermixed_args()

    # Debugging
    print(args.files, file=sys.stderr)
    print(args, file=sys.stderr)

    # TODO: Add clipboard uploader

    # Quit if no destinations are given
    if not args.destinations:
        parser.error("at least one destination is required")

    for destination in args.destinations:
        for file in args.files:
            destination.upload(file)
            file.seek(0)


if __name__ == "__main__":
    main()

# vim: shiftwidth=4 expandtab autoindent
