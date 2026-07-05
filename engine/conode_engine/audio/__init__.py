"""audio — capture, features, modmatrix, prompt binding. (M4, PLAN §3)"""
from .capture import AudioCapture
from .features import FEATURES, FeatureExtractor
from .modmatrix import LFO, ModCell, ModMatrix
from .prompt_binding import bind_prompt, parse_bindings

__all__ = [
    "AudioCapture",
    "FeatureExtractor",
    "FEATURES",
    "ModMatrix",
    "ModCell",
    "LFO",
    "bind_prompt",
    "parse_bindings",
]
