"""nodes — 노드당 1파일, Processor 상속, ParamSpec 선언 필수. (R4)"""
from .audio_in import AudioIn
from .blend import Blend
from .camera import Camera
from .canny import Canny
from .color_grade import ColorGrade
from .crossfade import Crossfade
from .depth import Depth
from .feedback import FeedbackLoop
from .gesture_recognizer import GestureRecognizer
from .hand_tracker import HandTracker
from .image import Image
from .live_diffusion import LiveDiffusion
from .mapped_output import MappedOutput
from .mask_compose import MaskCompose
from .mod_matrix import ModMatrix
from .pose import Pose
from .recorder import Recorder
from .region_mask import RegionMask
from .segmentation import Segmentation
from .style_preset import StylePreset
from .switch import Switch

__all__ = [
    "AudioIn", "Blend", "Camera", "Canny", "ColorGrade", "Crossfade", "Depth",
    "FeedbackLoop", "GestureRecognizer", "HandTracker", "Image", "LiveDiffusion",
    "MappedOutput", "MaskCompose", "ModMatrix", "Pose", "Recorder", "RegionMask",
    "Segmentation", "StylePreset", "Switch",
]
