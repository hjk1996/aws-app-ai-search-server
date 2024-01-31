from pydantic import BaseModel, validator
from typing import List, Optional


# Label Detection


class BoundingBox(BaseModel):
    Height: float
    Left: float
    Top: float
    Width: float


class Instance(BaseModel):
    BoundingBox: Optional[BoundingBox]
    Confidence: Optional[float] = None


class Label(BaseModel):
    Aliases: List[str] = []
    Categories: List[str] = []
    Confidence: float
    Instances: List[Instance] = []
    Name: str
    Parents: List[str] = []

    @validator("Aliases", "Categories", "Parents", pre=True, each_item=True)
    def extract_name(cls, v):
        return v["Name"] if isinstance(v, dict) and "Name" in v else v


# Text Detection


class Point(BaseModel):
    X: float
    Y: float


class BoundingBox(BaseModel):
    Height: float
    Left: float
    Top: float
    Width: float


class Geometry(BaseModel):
    BoundingBox: BoundingBox
    Polygon: List[Point]


class Text(BaseModel):
    Confidence: float
    DetectedText: str
    Geometry: Geometry
    Id: int
    ParentId: Optional[int] = None
    Type: str


# Face Detail


class AgeRange(BaseModel):
    High: int
    Low: int


class Emotion(BaseModel):
    Confidence: float
    Type: str


class EyeDirection(BaseModel):
    Confidence: float
    Pitch: float
    Yaw: float


class Pose(BaseModel):
    Pitch: float
    Roll: float
    Yaw: float


class Quality(BaseModel):
    Brightness: float
    Sharpness: float


class Landmark(BaseModel):
    Type: str
    X: float
    Y: float


class FaceDetails(BaseModel):
    AgeRange: AgeRange
    Beard: bool
    BoundingBox: BoundingBox
    Confidence: float
    Emotions: List[Emotion]
    EyeDirection: EyeDirection
    Eyeglasses: bool
    EyesOpen: bool
    FaceOccluded: bool
    Gender: str
    Landmarks: List[Landmark]
    MouthOpen: bool
    Mustache: bool
    Pose: Pose
    Quality: Quality
    Smile: bool
    Sunglasses: bool

    @validator(
        "Beard",
        "Eyeglasses",
        "EyesOpen",
        "FaceOccluded",
        "MouthOpen",
        "Mustache",
        "Smile",
        "Sunglasses",
        pre=True,
    )
    def extract_bool_value(cls, v):
        return v.get("Value") if isinstance(v, dict) and "Value" in v else v

    @validator("Gender", pre=True)
    def extract_str_value(cls, v):
        return v.get("Value") if isinstance(v, dict) and "Value" in v else v


# Image Metadata


class ImageMetadata(BaseModel):
    id: str
    labels: List[Label]
    texts: Optional[List[Text]] = []  # 선택적 필드
    face_details: Optional[List[FaceDetails]] = []  # 선택적 필드
