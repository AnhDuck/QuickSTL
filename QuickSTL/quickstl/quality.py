import math

from .logging_utils import log

QUALITY_PRESETS = {
    "Low": {
        "surfaceDeviation_cm": 0.25,
        "normalDeviation_deg": 30.0,
        "maximumEdgeLength_cm": 0.0,
        "aspectRatio": 0.95,
    },
    "Medium": {
        "surfaceDeviation_cm": 0.05,
        "normalDeviation_deg": 20.0,
        "maximumEdgeLength_cm": 0.0,
        "aspectRatio": 0.85,
    },
    "High": {
        "surfaceDeviation_cm": 0.01,
        "normalDeviation_deg": 10.0,
        "maximumEdgeLength_cm": 0.0,
        "aspectRatio": 0.65,
    },
    "VeryHigh": {
        "surfaceDeviation_cm": 0.0025,
        "normalDeviation_deg": 5.0,
        "maximumEdgeLength_cm": 0.0,
        "aspectRatio": 0.25,
    },
    "Ultra": {
        "surfaceDeviation_cm": 0.001,
        "normalDeviation_deg": 3.0,
        "maximumEdgeLength_cm": 0.0,
        "aspectRatio": 0.20,
    },
}


def deg_to_rad(value: float) -> float:
    return float(value) * math.pi / 180.0


def apply_obj_quality(opts, quality: str) -> dict:
    """Only sets numeric properties; lets Fusion mark refinement as custom internally."""
    preset = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["High"])
    applied = {
        "mode": quality,
        "target": "OBJ→STL",
        "custom": {
            "surfaceDeviation_cm": preset["surfaceDeviation_cm"],
            "normalDeviation_deg": preset["normalDeviation_deg"],
            "maximumEdgeLength_cm": preset["maximumEdgeLength_cm"],
            "aspectRatio": preset["aspectRatio"],
            "scale_mm": 10.0,  # OBJ default centimeters -> mm
        },
    }
    try:
        opts.surfaceDeviation = float(preset["surfaceDeviation_cm"])
    except Exception as exc:
        log(f"apply_obj_quality surfaceDeviation set failed: {exc}")
    try:
        opts.normalDeviation = float(deg_to_rad(preset["normalDeviation_deg"]))
    except Exception as exc:
        log(f"apply_obj_quality normalDeviation set failed: {exc}")
    try:
        opts.maximumEdgeLength = float(preset["maximumEdgeLength_cm"])
    except Exception as exc:
        log(f"apply_obj_quality maximumEdgeLength set failed: {exc}")
    try:
        opts.aspectRatio = float(preset["aspectRatio"])
    except Exception as exc:
        log(f"apply_obj_quality aspectRatio set failed: {exc}")
    return applied
