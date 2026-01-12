"""Fusion 360 entrypoint for the QuickSTL add-in."""

import os
import sys

ADDIN_DIR = os.path.dirname(os.path.realpath(__file__))
if ADDIN_DIR not in sys.path:
    sys.path.insert(0, ADDIN_DIR)

from quickstl.entrypoint import run, stop

__all__ = ["run", "stop"]
