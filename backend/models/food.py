"""
美食模型
"""

from typing import List, Dict
from .base import BaseModel


class Food(BaseModel):
    """
    美食模型

    属性:
        id: 美食ID
        name: 美食名称
        cuisine: 菜系（川菜/粤菜/湘菜等）
        restaurant: 餐厅/窗口名称
        campus_id: 所属校区ID
        building_id: 所属建筑ID
        x, y: 坐标
        distance: 距参考点的距离（查询时计算）
        heat: 热度
        rating: 评分
        price: 价格（可选）
        image_url: 图片URL
    """

    CUISINES = ['川菜', '粤菜', '湘菜', '鲁菜', '苏菜', '浙菜', '闽菜', '徽菜',
                '东北菜', '西北菜', '清真', '日料', '韩料', '西餐', '快餐']

    def __init__(self, id: str, name: str,
                 cuisine: str = '',
                 restaurant: str = '',
                 campus_id: str = None,
                 building_id: str = None,
                 x: float = 0, y: float = 0,
                 distance: float = None,
                 heat: int = 0, rating: float = 5.0,
                 price: float = None,
                 image_url: str = None,
                 location_node_id: str = None,
                 **kwargs):
        super().__init__(id, **kwargs)
        self.name = name
        self.cuisine = cuisine
        self.restaurant = restaurant
        self.campus_id = campus_id
        self.building_id = building_id
        self.x = x
        self.y = y
        self.distance = distance
        self.heat = heat
        self.rating = rating
        self.price = price
        self.image_url = image_url
        self.location_node_id = location_node_id

    @classmethod
    def from_dict(cls, data: Dict):
        if not data:
            return None
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            cuisine=data.get('cuisine', ''),
            restaurant=data.get('restaurant', ''),
            campus_id=data.get('campus_id'),
            building_id=data.get('building_id'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            distance=data.get('distance'),
            heat=data.get('heat', 0),
            rating=data.get('rating', 5.0),
            price=data.get('price'),
            image_url=data.get('image_url'),
            location_node_id=data.get('location_node_id')
        )

    @staticmethod
    def is_valid_cuisine(cuisine: str) -> bool:
        """检查菜系是否有效"""
        return cuisine in Food.CUISINES
