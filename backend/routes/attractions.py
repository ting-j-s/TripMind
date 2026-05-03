"""
景点路由 - 景点列表、搜索、推荐
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify

from backend.data import get_loader
from backend.core import top_k
from backend.algorithms import fuzzy_search

attractions_bp = Blueprint('attractions', __name__)


@attractions_bp.route('/attractions', methods=['GET'])
def get_attractions():
    """
    获取景点列表

    查询参数:
        campus_id: 校园ID（可选）
        sort: 排序方式 heat/rating
        limit: 返回数量（默认10）
        offset: 偏移量（分页用）
    """
    campus_id = request.args.get('campus_id')
    sort_by = request.args.get('sort', 'heat')  # heat 或 rating
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    loader = get_loader()
    attractions = loader.get_all_attractions()

    # 按校园过滤
    if campus_id:
        attractions = [a for a in attractions if a.campus_id == campus_id]

    # 排序
    if sort_by == 'rating':
        attractions = top_k(attractions, limit,
                           key=lambda x: x.rating, reverse=True)
    else:  # 默认按热度
        attractions = top_k(attractions, limit,
                           key=lambda x: x.heat, reverse=True)

    # 分页
    total = len(attractions)
    attractions = attractions[offset:offset + limit]

    return jsonify({
        'code': 200,
        'data': {
            'items': [a.to_dict() for a in attractions],
            'total': total,
            'limit': limit,
            'offset': offset
        },
        'message': 'success'
    })


@attractions_bp.route('/attractions/<attraction_id>', methods=['GET'])
def get_attraction(attraction_id):
    """获取景点详情"""
    loader = get_loader()
    attraction = loader.get_attraction(attraction_id)

    if not attraction:
        return jsonify({'code': 404, 'message': '景点不存在', 'data': None})

    # 增加热度
    attraction.increment_heat()
    loader.save_attractions()

    return jsonify({
        'code': 200,
        'data': attraction.to_dict(),
        'message': 'success'
    })


@attractions_bp.route('/attractions/search', methods=['GET'])
def search_attractions():
    """
    搜索景点

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
    attractions = loader.get_all_attractions()

    # 转换为字典列表
    items = [a.to_dict() for a in attractions]

    # 模糊搜索
    results = fuzzy_search(items, query, fields=['name', 'tags', 'description'], limit=limit)

    return jsonify({
        'code': 200,
        'data': {
            'items': results,
            'total': len(results),
            'query': query
        },
        'message': 'success'
    })


@attractions_bp.route('/recommend', methods=['GET'])
def recommend():
    """
    个性化推荐

    根据用户兴趣推荐景点

    查询参数:
        user_id: 用户ID（可选，不登录则按热度推荐）
        limit: 返回数量（默认10）
    """
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))

    loader = get_loader()
    attractions = loader.get_all_attractions()

    # 如果有用户，按兴趣推荐
    if user_id:
        user = loader.get_user(user_id)
        if user and user.interests:
            # 找出匹配用户兴趣的景点
            matched = []
            unmatched = []

            for a in attractions:
                if any(interest in a.tags for interest in user.interests):
                    matched.append(a)
                else:
                    unmatched.append(a)

            # 匹配的兴趣景点排前面，按热度排序
            matched = top_k(matched, limit, key=lambda x: x.heat, reverse=True)
            unmatched = top_k(unmatched, limit, key=lambda x: x.heat, reverse=True)

            attractions = matched + unmatched
        else:
            attractions = top_k(attractions, limit, key=lambda x: x.heat, reverse=True)
    else:
        # 无用户，按热度推荐
        attractions = top_k(attractions, limit, key=lambda x: x.heat, reverse=True)

    return jsonify({
        'code': 200,
        'data': {
            'items': [a.to_dict() for a in attractions[:limit]],
            'total': len(attractions[:limit])
        },
        'message': 'success'
    })


@attractions_bp.route('/campuses', methods=['GET'])
def get_campuses():
    """获取校园列表"""
    loader = get_loader()
    campuses = loader.get_all_campuses()

    return jsonify({
        'code': 200,
        'data': {
            'items': [c.to_dict() for c in campuses],
            'total': len(campuses)
        },
        'message': 'success'
    })
