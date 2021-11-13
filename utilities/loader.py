import json
import os
import typing


def load_json(directory: typing.Union[os.PathLike, str, bytes]) -> dict:
    """Load json file"""
    with open(directory) as file:
        contents = json.load(file)

    """Return contents as dict."""
    return contents
