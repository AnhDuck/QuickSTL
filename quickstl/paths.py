import os

from .constants import CONFIG_FILENAME, RES_DIR, TOAST_HTML_FN, TOAST_JSON_FN


def addin_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def resource_path(*parts) -> str:
    return os.path.join(addin_dir(), RES_DIR, *parts)


def toast_html_path() -> str:
    return resource_path(TOAST_HTML_FN)


def toast_json_path() -> str:
    return resource_path(TOAST_JSON_FN)


def icon_folder() -> str:
    return os.path.join(addin_dir(), "resources", "QuickSTL")


def config_path() -> str:
    return os.path.join(addin_dir(), CONFIG_FILENAME)


def debug_path() -> str:
    return os.path.join(addin_dir(), "debug.json")
