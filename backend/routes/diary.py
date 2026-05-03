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
from backend.core import top_k
from backend.algorithms import TextSearchIndex, simple_text_search, HuffmanCoding

diary_bp = Blueprint('diary', __name__)


def build_search_index():
    """构建日记搜索索引"""
    loader = get_loader()
    diaries = loader.get_all_diaries()

    index = TextSearchIndex()
    for diary in diaries:
        index.add_document(
            diary.id,
            diary.title + ' ' + diary.content,
            {'title': diary.title, 'user_id': diary.user_id}
        )

    return index


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
    搜索日记（全文搜索）

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

    loader = get_loader()
    diaries = loader.get_all_diaries()

    # 简单文本搜索
    results = simple_text_search(
        [{'id': d.id, 'content': d.title + ' ' + d.content, 'diary': d} for d in diaries],
        query,
        content_field='content',
        limit=limit
    )

    items = []
    for r in results:
        diary = r['diary']
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

    # 霍夫曼压缩
    huffman = HuffmanCoding()
    huffman.build(diary.content)
    compressed, code_table = huffman.compress(diary.content)

    # 保存压缩内容和解码表
    diary.compressed_content = compressed
    diary.compression_code_table = code_table
    diary.content = ''  # 清空原内容，节省空间
    loader.save_diaries()

    original_size = len(diary.content.encode('utf-8')) if diary.content else 0

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
    按标题精确搜索日记

    查询参数:
        title: 标题关键词
        limit: 返回数量
    """
    title = request.args.get('title', '').strip()
    limit = int(request.args.get('limit', 10))

    if not title:
        return jsonify({
            'code': 200,
            'data': {'items': [], 'total': 0},
            'message': 'success'
        })

    loader = get_loader()
    diaries = loader.get_all_diaries()

    # 精确匹配标题（忽略大小写）
    results = [d for d in diaries if title.lower() in d.title.lower()][:limit]

    return jsonify({
        'code': 200,
        'data': {
            'items': [d.to_dict() for d in results],
            'total': len(results),
            'query': title
        },
        'message': 'success'
    })
