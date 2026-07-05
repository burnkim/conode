"""nodes — 노드당 1파일, Processor 상속, ParamSpec 선언 필수. (R4)"""
from .camera import Camera
from .canny import Canny
from .depth import Depth
from .gesture_recognizer import GestureRecognizer
from .hand_tracker import HandTracker
from .live_diffusion import LiveDiffusion
from .pose import Pose
from .region_mask import RegionMask
from .segmentation import Segmentation

__all__ = [
    "Camera",
    "Canny",
    "Depth",
    "GestureRecognizer",
    "HandTracker",
    "LiveDiffusion",
    "Pose",
    "RegionMask",
    "Segmentation",
]
