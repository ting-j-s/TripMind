"""
日记路由 - 日记CRUD、搜索、评分
"""

import uuid
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify

from backend.data import get_loader
from backend.models.diary import Diary
from backend.core import top_k, HashTable
from backend.algorithms import TextSearchIndex, simple_text_search, HuffmanCoding

diary_bp = Blueprint('diary', __name__)

# 搜索索引缓存
_search_index = None
_search_index_dirty = True  # 初始为脏，需要重建

# 标题索引缓存（HashTable）
_title_index = None
_title_index_dirty = True  # 初始为脏，需要重建


def normalize_title(title):
    """
    归一化标题用于精确查询
    - 转小写
    - 去除首尾空格
    """
    if not title:
        return ''
    return title.lower().strip()


def build_title_index():
    """构建标题索引（使用 HashTable）"""
    global _title_index, _title_index_dirty

    loader = get_loader()
    diaries = loader.get_all_diaries()

    index = HashTable(size=100)
    for diary in diaries:
        key = normalize_title(diary.title)
        if key:
            existing = index.get(key, [])
            if isinstance(existing, list):
                existing.append(diary.id)
                index.put(key, existing)
            else:
                index.put(key, [diary.id])

    _title_index = index
    _title_index_dirty = False
    return index


def get_title_index():
    """获取标题索引（懒加载，脏时重建）"""
    global _title_index, _title_index_dirty

    if _title_index is None or _title_index_dirty:
        build_title_index()
    return _title_index


def mark_title_index_dirty():
    """标记标题索引为脏，需要重建"""
    global _title_index_dirty
    _title_index_dirty = True


def build_search_index():
    """构建日记搜索索引（使用倒排索引）"""
    global _search_index, _search_index_dirty

    loader = get_loader()
    diaries = loader.get_all_diaries()

    index = TextSearchIndex()
    for diary in diaries:
        # 索引标题+内容，便于全文搜索
        index.add_document(
            diary.id,
            diary.title + ' ' + diary.content,
            {'title': diary.title, 'user_id': diary.user_id}
        )

    _search_index = index
    _search_index_dirty = False
    return index


def get_search_index():
    """获取搜索索引（懒加载，脏时重建）"""
    global _search_index, _search_index_dirty

    if _search_index is None or _search_index_dirty:
        build_search_index()
    return _search_index


def mark_search_index_dirty():
    """标记搜索索引为脏，需要重建"""
    global _search_index_dirty
    _search_index_dirty = True


@diary_bp.route('/diaries', methods=['GET'])
def get_diaries():
    """
    获取日记列表

    查询参数:
        sort: 排序方式 heat/rating/time
        limit: 返回数量
        offset: 偏移量
        location_id: 按景点筛选
    """
    sort_by = request.args.get('sort', 'heat')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))
    location_id = request.args.get('location_id')

    loader = get_loader()
    diaries = loader.get_all_diaries()

    # 按景点筛选
    if location_id:
        diaries = [d for d in diaries if d.location_id == location_id]

    # 排序
    if sort_by == 'rating':
        diaries = top_k(diaries, limit,
                       key=lambda x: x.get_average_rating(), reverse=True)
    elif sort_by == 'time':
        diaries = sorted(diaries, key=lambda x: x.create_time or '', reverse=True)
    else:  # 默认按热度
        diaries = top_k(diaries, limit,
                       key=lambda x: x.view_count, reverse=True)

    total = len(diaries)
    diaries = diaries[offset:offset + limit]

    return jsonify({
        'code': 200,
        'data': {
            'items': [d.to_dict() for d in diaries],
            'total': total,
            'limit': limit,
            'offset': offset
        },
        'message': 'success'
    })


@diary_bp.route('/diaries/search', methods=['GET'])
def search_diaries():
    """
    搜索日记（全文搜索 - 倒排索引）

    查询参数:
        q: 搜索关键词
        limit: 返回数量
    """
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 10))

    if not query:
        return jsonify({
            'code': 200,
            'data': {'items': [], 'total': 0},
            'message': 'success'
        })

    # 使用倒排索引搜索
    index = get_search_index()
    results = index.search(query, limit)

    # 获取日记完整对象
    loader = get_loader()
    items = []
    for r in results:
        diary = loader.get_diary(r['doc_id'])
        if diary:
            items.append(diary.to_dict())

    return jsonify({
        'code': 200,
        'data': {
            'items': items,
            'total': len(items),
            'query': query
        },
        'message': 'success'
    })


@diary_bp.route('/diary', methods=['POST'])
def create_diary():
    """
    创建日记

    请求:
        {
            "user_id": "用户ID",
            "title": "标题",
            "content": "内容",
            "images": ["url1", "url2"],
            "videos": ["url1"],
            "location_id": "景点ID"
        }
    """
    data = request.get_json()

    user_id = data.get('user_id')
    title = data.get('title', '').strip()
    content = data.get('content', '')

    if not user_id:
        return jsonify({'code': 401, 'message': '请先登录', 'data': None})

    if not title:
        return jsonify({'code': 400, 'message': '标题不能为空', 'data': None})

    loader = get_loader()
    user = loader.get_user(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None})

    # 创建日记
    diary_id = f"diary_{uuid.uuid4().hex[:8]}"
    diary = Diary(
        id=diary_id,
        user_id=user_id,
        title=title,
        content=content,
        images=data.get('images', []),
        videos=data.get('videos', []),
        location_id=data.get('location_id'),
        create_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        view_count=0,
        ratings=[]
    )

    # 可选：压缩存储内容
    if content:
        huffman = HuffmanCoding()
        huffman.build(content)
        compressed, _ = huffman.compress(content)
        diary.compressed_content = compressed

    loader.add_diary(diary)
    mark_search_index_dirty()  # 全文搜索索引需要重建
    mark_title_index_dirty()  # 标题索引需要重建

    # 更新用户的已访问景点
    if diary.location_id:
        user.add_visited(diary.location_id)
        loader.save_users()

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': {'diary_id': diary_id}
    })


@diary_bp.route('/diary/<diary_id>', methods=['GET'])
def get_diary(diary_id):
    """获取日记详情"""
    loader = get_loader()
    diary = loader.get_diary(diary_id)

    if not diary:
        return jsonify({'code': 404, 'message': '日记不存在', 'data': None})

    # 增加浏览量
    diary.increment_view()
    loader.save_diaries()

    return jsonify({
        'code': 200,
        'data': diary.to_dict(),
        'message': 'success'
    })


@diary_bp.route('/diary/<diary_id>', methods=['PUT'])
def update_diary(diary_id):
    """
    更新日记

    请求:
        {
            "user_id": "用户ID",
            "title": "标题",
            "content": "内容"
        }
    """
    data = request.get_json()
    user_id = data.get('user_id')

    loader = get_loader()
    diary = loader.get_diary(diary_id)

    if not diary:
        return jsonify({'code': 404, 'message': '日记不存在', 'data': None})

    if diary.user_id != user_id:
        return jsonify({'code': 403, 'message': '无权限修改', 'data': None})

    # 更新字段
    if data.get('title'):
        diary.title = data['title']
    if data.get('content'):
        diary.content = data['content']
    if 'images' in data:
        diary.images = data['images']
    if 'videos' in data:
        diary.videos = data['videos']

    mark_search_index_dirty()  # 全文搜索索引需要重建
    mark_title_index_dirty()  # 标题索引需要重建
    loader.save_diaries()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': diary.to_dict()
    })


@diary_bp.route('/diary/<diary_id>', methods=['DELETE'])
def delete_diary(diary_id):
    """删除日记"""
    user_id = request.args.get('user_id')

    loader = get_loader()
    diary = loader.get_diary(diary_id)

    if not diary:
        return jsonify({'code': 404, 'message': '日记不存在', 'data': None})

    if diary.user_id != user_id:
        return jsonify({'code': 403, 'message': '无权限删除', 'data': None})

    loader.delete_diary(diary_id)
    mark_search_index_dirty()  # 全文搜索索引需要重建
    mark_title_index_dirty()  # 标题索引需要重建

    return jsonify({
        'code': 200,
        'message': '删除成功',
        'data': None
    })


@diary_bp.route('/diary/<diary_id>/rate', methods=['POST'])
def rate_diary(diary_id):
    """
    评分日记

    请求:
        {
            "rating": 4.5
        }
    """
    data = request.get_json()
    rating = float(data.get('rating', 0))

    if rating < 1 or rating > 5:
        return jsonify({'code': 400, 'message': '评分需在1-5之间', 'data': None})

    loader = get_loader()
    diary = loader.get_diary(diary_id)

    if not diary:
        return jsonify({'code': 404, 'message': '日记不存在', 'data': None})

    diary.add_rating(rating)
    loader.save_diaries()

    return jsonify({
        'code': 200,
        'message': '评分成功',
        'data': {
            'average_rating': diary.get_average_rating(),
            'ratings_count': len(diary.ratings)
        }
    })


@diary_bp.route('/diary/<diary_id>/compress', methods=['POST'])
def compress_diary(diary_id):
    """
    压缩日记内容（霍夫曼编码）

    请求:
        {
            "user_id": "用户ID"  // 可选，用于权限校验
        }

    返回:
        {
            "code": 200,
            "data": {
                "original_size": 原始大小,
                "compressed_size": 压缩后大小,
                "compression_ratio": 压缩比
            }
        }
    """
    loader = get_loader()
    diary = loader.get_diary(diary_id)

    if not diary:
        return jsonify({'code': 404, 'message': '日记不存在', 'data': None})

    if not diary.content:
        return jsonify({'code': 400, 'message': '日记内容为空', 'data': None})

    # 保存原文用于压缩和计算原始大小（在清空content之前）
    original_content = diary.content
    original_size = len(original_content.encode('utf-8'))

    # 霍夫曼压缩
    huffman = HuffmanCoding()
    huffman.build(original_content)
    compressed, code_table = huffman.compress(original_content)

    # 保存压缩内容和解码表
    diary.compressed_content = compressed
    diary.compression_code_table = code_table
    diary.content = ''  # 清空原内容，节省空间
    loader.save_diaries()

    return jsonify({
        'code': 200,
        'message': '压缩成功',
        'data': {
            'original_size': original_size,
            'compressed_size': len(compressed),
            'compression_ratio': len(compressed) / original_size if original_size > 0 else 0,
            'code_table_size': len(code_table)
        }
    })


@diary_bp.route('/diary/<diary_id>/decompress', methods=['POST'])
def decompress_diary(diary_id):
    """
    解压日记内容

    请求:
        {
            "user_id": "用户ID"  // 可选，用于权限校验
        }

    返回:
        {
            "code": 200,
            "data": {
                "content": "解压后的原文"
            }
        }
    """
    loader = get_loader()
    diary = loader.get_diary(diary_id)

    if not diary:
        return jsonify({'code': 404, 'message': '日记不存在', 'data': None})

    if not diary.compressed_content:
        # 没有压缩内容，直接返回原文
        return jsonify({
            'code': 200,
            'message': '无需解压',
            'data': {
                'content': diary.content,
                'compressed': False
            }
        })

    # 霍夫曼解压
    huffman = HuffmanCoding()
    # 需要重新构建解码表 - 这里简化处理，实际应该存储code_table
    # 由于HuffmanCoding在compress时没有保存code_table，需要用另一种方式
    # 方案：使用压缩时自带的code_table信息

    # 实际上，HuffmanCoding.decompress需要code_table
    # 但我们存储的compressed_content只是bytes，没有code_table
    # 这里需要修改存储策略 - 保存code_table

    # 简化处理：如果有compressed_content但没有code_table，返回错误
    if not hasattr(diary, 'compression_code_table') or not diary.compression_code_table:
        return jsonify({'code': 500, 'message': '编码表丢失，无法解压', 'data': None})

    decompressed = huffman.decompress(diary.compressed_content, diary.compression_code_table)

    return jsonify({
        'code': 200,
        'message': '解压成功',
        'data': {
            'content': decompressed,
            'compressed': True
        }
    })


@diary_bp.route('/diaries/title', methods=['GET'])
def search_by_title():
    """
    按标题精确搜索日记（使用 HashTable 索引）

    查询参数:
        title: 标题（精确匹配，忽略大小写和首尾空格）
        limit: 返回数量
    """
    original_query = request.args.get('title', '')
    limit = int(request.args.get('limit', 10))

    normalized_title = normalize_title(original_query)

    if not normalized_title:
        return jsonify({
            'code': 400,
            'data': {'items': [], 'total': 0},
            'message': 'title参数不能为空'
        })

    # 使用 HashTable 精确查询
    title_index = get_title_index()
    diary_ids = title_index.get(normalized_title, [])

    # 获取完整 Diary 对象
    loader = get_loader()
    items = []
    for diary_id in diary_ids:
        diary = loader.get_diary(diary_id)
        if diary:
            items.append(diary.to_dict())

    # 截断到 limit
    items = items[:limit]

    return jsonify({
        'code': 200,
        'data': {
            'items': items,
            'total': len(items),
            'query': original_query
        },
        'message': 'success'
    })
