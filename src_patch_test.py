import json
from typing import List, Dict, Any, Optional

PROJECT_META_KEY = "METADATA_JSON"
POINTS_KEY = "POINTS_JSON"

class Point:
    def __init__(self, id: int, x: float, y: float, shape: str = "circle", size: float = 5.0, measures: Optional[Dict[str, float]] = None, status: str = "ok"):
        self.id = id
        self.x = x
        self.y = y
        self.shape = shape
        self.size = size
        self.measures = measures or {}
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "shape": self.shape,
            "size": self.size,
            "measures": self.measures,
            "status": self.status,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        return Point(
            id=int(d.get("id")),
            x=float(d.get("x")),
            y=float(d.get("y")),
            shape=d.get("shape","circle"),
            size=float(d.get("size",5.0)),
            measures=d.get("measures",{}),
            status=d.get("status","ok"),
        )

class Metadata:
    def __init__(self, version: str, app_version: str, state: str, project_info: Dict[str, Any], timestamps: Dict[str, Any], image_info: Dict[str, Any], points_info: List[Point], statistics: Dict[str, Any]):
        self.version = version
        self.app_version = app_version
        self.state = state
        self.project_info = project_info
        self.timestamps = timestamps
        self.image_info = image_info
        self.points_info = points_info
        self.statistics = statistics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "app_version": self.app_version,
            "state": self.state,
            "project_info": self.project_info,
            "timestamps": self.timestamps,
            "image_info": self.image_info,
            "points_info": [p.to_dict() for p in self.points_info],
            "statistics": self.statistics,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]):
        pts = [Point.from_dict(p) for p in d.get("points_info", [])]
        return Metadata(
            version=d.get("version","2.0"),
            app_version=d.get("app_version","0.0"),
            state=d.get("state","idle"),
            project_info=d.get("project_info", {}),
            timestamps=d.get("timestamps", {}),
            image_info=d.get("image_info", {}),
            points_info=pts,
            statistics=d.get("statistics", {}),
        )

def serialize_metadata(meta: Metadata) -> str:
    return json.dumps(meta.to_dict(), indent=2)

def deserialize_metadata(data: str) -> Metadata:
    d = json.loads(data)
    return Metadata.from_dict(d)

def load_project(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    meta = Metadata.from_dict(data.get(PROJECT_META_KEY, {}))
    pts = [Point.from_dict(p) for p in data.get(POINTS_KEY, [])]
    return meta, pts

def save_project(filepath: str, meta: Metadata, points: List[Point]):
    data = {
        PROJECT_META_KEY: meta.to_dict(),
        POINTS_KEY: [p.to_dict() for p in points],
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
