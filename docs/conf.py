"""Sphinx configuration for python_awair."""
# pylint: skip-file
import os
import sys

import sphinx_readable_theme

sys.path.insert(0, os.path.abspath(".."))

project = "python_awair"
copyright = "2019-2020, Andrew Hayworth"
author = "Andrew Hayworth"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    # "sphinx.ext.linkcode",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]
templates_path = ["_templates"]

todo_include_todos = True

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme_path = [sphinx_readable_theme.get_html_theme_path()]
html_theme = "readable"

html_static_path = ["_static"]

intersphinx_mapping = {"aiohttp": ("https://aiohttp.readthedocs.io/en/stable/", None)}

master_doc = "index"


def linkcode_resolve(domain, info):  # type: ignore
    """Return github.com link for module."""
    if domain != "py" or "module" not in info:
        return None

    filename = info["module"].replace(".", "/")
    if filename == "python_awair":
        filename += "/__init__.py"
    else:
        filename += ".py"

    return "https://github.com/ahayworth/python_awair/tree/master/" + filename
