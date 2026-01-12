ADDIN_NAME = "Quick STL"
ADDIN_VERSION = "3.00.0"
IDLE_TIMEOUT_S = 30

CMD_ID = "quickstl_export_cmd"
CMD_NAME = "Quick STL"
CONFIG_FILENAME = "config.json"

# Legacy STL path always writes Binary STL
BINARY_FORMAT = True

# Toast config
TOAST_ID = "quickstl_toast"
TOAST_TITLE = "STL Exported"
TOAST_MS = 15000
TOAST_W = 500
TOAST_H = 525

# Resource paths (static HTML + JSON + three.js)
RES_DIR = "resources"
TOAST_HTML_FN = "quickstl_toast.html"
TOAST_JSON_FN = "quickstl_toast.json"
PREVIEW_DIR = "preview"
THREE_FILE = "three.min.js"

SLICER_CHOICES = ["OrcaSlicer", "SuperSlicer", "Bambu Studio"]
QUALITY_CHOICES = ["Legacy", "Low", "Medium", "High", "VeryHigh", "Ultra"]

DEFAULT_CONFIG = {
    "export_dir": "",
    "prefer_selection": True,
    "per_doc_folders": {},
    "clicks_saved": 0,
    "quality": "Legacy",  # Legacy uses STL Only; other presets use OBJ→STL
    "slicer": {
        "name": "OrcaSlicer",
        "paths": {name: "" for name in SLICER_CHOICES},
    },
}
