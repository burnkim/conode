"""nodes — 노드당 1파일, Processor 상속, ParamSpec 선언 필수. (R4)"""
from .camera import Camera
from .canny import Canny

__all__ = ["Camera", "Canny"]
