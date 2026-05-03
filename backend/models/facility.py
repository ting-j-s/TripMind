"""
服务设施模型
"""

from typing import Dict
from .base import BaseModel


class Facility(BaseModel):
    """
    服务设施模型

    属性:
        id: 设施ID
        name: 名称
        type: 类型（超市/洗手间/餐厅等）
        building_id: 所属建筑ID
        campus_id: 所属校区ID
        x, y: 坐标
        floor: 楼层（室内）
    """

    FACILITY_TYPES = [
        '超市', '洗手间', '餐厅', '食堂', '图书馆',
        '咖啡馆', 'ATM', '医院', '售票处', '停车场',
        '自行车棚', '电瓶车停靠点', '服务中心', '游客中心'
    ]

    def __init__(self, id: str, name: str,
                 type: str,
                 building_id: str = None,
                 campus_id: str = None,
                 x: float = 0, y: float = 0,
                 floor: int = 0,
                 location_node_id: str = None,
                 **kwargs):
        super().__init__(id, **kwargs)
        self.name = name
        self.type = type
        self.building_id = building_id
        self.campus_id = campus_id
        self.x = x
        self.y = y
        self.floor = floor
        self.location_node_id = location_node_id

    @classmethod
    def from_dict(cls, data: Dict):
        if not data:
            return None
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            type=data.get('type', ''),
            building_id=data.get('building_id'),
            campus_id=data.get('campus_id'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            floor=data.get('floor', 0),
            location_node_id=data.get('location_node_id')
        )

    @staticmethod
    def is_valid_type(facility_type: str) -> bool:
        """检查设施类型是否有效"""
        return facility_type in Facility.FACILITY_TYPES
