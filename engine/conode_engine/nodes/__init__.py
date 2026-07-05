"""nodes — 노드당 1파일, Processor 상속, ParamSpec 선언 필수. (R4)"""
from .camera import Camera
from .canny import Canny
from .depth import Depth
from .live_diffusion import LiveDiffusion
from .pose import Pose
from .segmentation import Segmentation

__all__ = ["Camera", "Canny", "Depth", "LiveDiffusion", "Pose", "Segmentation"]
