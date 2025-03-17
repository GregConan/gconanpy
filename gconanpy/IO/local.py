
#!/usr/bin/env python3

"""
Functions/classes to import/export data from/to files on the local filesystem.
Overlaps significantly with:
    audit-ABCC/src/utilities.py, \
    abcd-bids-tfmri-pipeline/src/pipeline_utilities.py, etc.
Greg Conan: gregmconan@gmail.com
Created: 2025-01-26
Updated: 2025-03-14
"""
# Import standard libraries
from glob import glob
import json
import os
import pdb
import shutil
from string import Formatter, Template
import sys
from typing import Any, Callable, Hashable, Iterable, Mapping


# NOTE All classes and functions below are in alphabetical order.


def extract_from_json(json_path: str) -> dict:
    """
    :param json_path: str, a valid path to a real readable .json file
    :return: dict, the contents of the file at json_path
    """
    with open(json_path) as infile:
        return json.load(infile)


def glob_and_copy(dest_dirpath: str, *path_parts_to_glob: str) -> None:
    """
    Collect all files matching a glob string, then copy those files
    :param dest_dirpath: String, a valid path of a directory to copy files into
    :param path_parts_to_glob: Unpacked list of strings which join to form a
                               glob string of a path to copy files from
    """
    for file_src in glob(os.path.join(*path_parts_to_glob)):
        shutil.copy(file_src, dest_dirpath)


class LoadedTemplate(Template):
    """ string.Template that \
        (1) can be loaded from a text file, and \
        (2) stores its own field/variable names.
    """
    parse = Formatter().parse

    def __init__(self, template_str: str):
        super().__init__(template_str)
        self.fields = self.get_field_names_in(template_str)

    @classmethod
    def get_field_names_in(cls, template_str: str) -> set[str]:
        """Get the name of every variables in template_str. Shamelessly \
            stolen from langchain_core.prompts.string.get_template_variables.

        :param template_str: str, the template string.
        :return: Set[str] of variable/field names in the template string.
        """
        return {field_name for _, field_name, _, _ in
                cls.parse(template_str) if field_name is not None}

    @classmethod
    def from_file_at(cls, txt_file_path: str) -> "LoadedTemplate":
        """
        :param txt_file_path: str, valid path to readable .txt file
        :return: LoadedTemplate loaded from the file at txt_file_path
        """
        with open(txt_file_path) as infile:
            return cls(infile.read())


def save_to_json(contents: Any, json_path: str) -> None:
    """
    :param json_path: str, a valid path to save a .json file at
    """
    with open(json_path, "w+") as outfile:
        json.dump(contents, outfile)
