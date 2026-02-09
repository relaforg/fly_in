from pydantic import BaseModel, Field
from typing import Tuple, List


class Hub(BaseModel):
    name: str = Field(min_length=1)
    coord: Tuple[int, int] = Field(max_length=2, min_length=2)
    zone_type: str = Field(default="normal")
    color: str = Field(default="white")
    max_drones: int = Field(ge=1, default=1)


class Connection(BaseModel):
    hubs: Tuple[Hub, Hub] = Field(max_length=2, min_length=2)
    max_link_capacity: int = Field(ge=1, default=1)


class Map(BaseModel):
    start: Hub = Field()
    end: Hub = Field()
    nb_drones: int = Field(ge=1)
    hubs: List[Hub] = Field(default_factory=list)
    connections: List[Connection] = Field(default_factory=list)
