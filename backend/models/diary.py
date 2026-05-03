"""
旅游日记模型
"""

from typing import List, Dict
from .base import BaseModel


class Diary(BaseModel):
    """
    旅游日记模型

    属性:
        id: 日记ID
        user_id: 作者用户ID
        title: 标题
        content: 内容
        images: 图片URL列表
        videos: 视频URL列表
        location_id: 关联的景点ID
        create_time: 创建时间
        view_count: 浏览量（热度）
        ratings: 评分列表
        compressed_content: 压缩后的内容（bytes）
    """

    def __init__(self, id: str, user_id: str, title: str,
                 content: str = '',
                 images: List[str] = None,
                 videos: List[str] = None,
                 location_id: str = None,
                 create_time: str = None,
                 view_count: int = 0,
                 ratings: List[float] = None,
                 compressed_content: bytes = None,
                 compression_code_table: Dict = None,
                 **kwargs):
        super().__init__(id, **kwargs)
        self.user_id = user_id
        self.title = title
        self.content = content
        self.images = images or []
        self.videos = videos or []
        self.location_id = location_id
        self.create_time = create_time
        self.view_count = view_count
        self.ratings = ratings or []
        self.compressed_content = compressed_content
        self.compression_code_table = compression_code_table or {}

    @classmethod
    def from_dict(cls, data: Dict):
        if not data:
            return None
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            title=data.get('title', ''),
            content=data.get('content', ''),
            images=data.get('images', []),
            videos=data.get('videos', []),
            location_id=data.get('location_id'),
            create_time=data.get('create_time'),
            view_count=data.get('view_count', 0),
            ratings=data.get('ratings', []),
            compressed_content=data.get('compressed_content'),
            compression_code_table=data.get('compression_code_table', {})
        )

    def to_dict(self) -> Dict:
        result = super().to_dict()
        # 移除压缩内容（不必要字段）
        if 'compressed_content' in result:
            del result['compressed_content']
        return result

    def increment_view(self):
        """增加浏览量"""
        self.view_count += 1

    def add_rating(self, rating: float):
        """添加评分"""
        if 1 <= rating <= 5:
            self.ratings.append(rating)

    def get_average_rating(self) -> float:
        """获取平均评分"""
        if not self.ratings:
            return 0
        return sum(self.ratings) / len(self.ratings)

    def get_heat(self) -> int:
        """获取热度（浏览量）"""
        return self.view_count
