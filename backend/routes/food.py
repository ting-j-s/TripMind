"""
美食路由 - 美食列表、搜索、推荐
"""

import sys
import os
import math
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify

from backend.data import get_loader
from backend.core import Graph, top_k
from backend.algorithms import dijkstra, fuzzy_search

food_bp = Blueprint('food', __name__)

# 道路网络图缓存
_road_graph_cache = None
_road_nodes_cache = None


def get_road_graph():
    """获取道路网络图（带缓存）"""
    global _road_graph_cache
    if _road_graph_cache is not None:
        return _road_graph_cache

    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'data')

    nodes = {}
    edges = []

    # 加载beijing_road_nodes.json获取节点坐标
    nodes_file = os.path.join(data_dir, 'beijing_road_nodes.json')
    if os.path.exists(nodes_file):
        with open(nodes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for node in data.get('nodes', []):
                nodes[node['id']] = {'x': node['x'], 'y': node['y']}

    # 加载roads.json获取边
    roads_file = os.path.join(data_dir, 'roads.json')
    if os.path.exists(roads_file):
        with open(roads_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for road in data.get('roads', []):
                edges.append({
                    'from': road['from'],
                    'to': road['to'],
                    'distance': road['distance'],
                    'ideal_speed': road.get('ideal_speed', 30),
                    'congestion': road.get('congestion', 1.0),
                    'road_types': road.get('road_types', ['步行'])
                })

    # 构建图
    g = Graph(directed=False)
    for node_id, coord in nodes.items():
        g.add_node(node_id, {'x': coord['x'], 'y': coord['y']})
    for edge in edges:
        g.add_edge(
            edge['from'], edge['to'],
            distance=edge['distance'],
            time=edge['distance'] / edge['ideal_speed'] * 3.6 if edge['ideal_speed'] > 0 else 0,
            ideal_speed=edge['ideal_speed'],
            congestion=edge['congestion'],
            road_types=edge['road_types']
        )

    _road_graph_cache = g
    return g


def get_road_nodes():
    """获取所有道路节点的坐标"""
    global _road_nodes_cache
    if _road_nodes_cache is not None:
        return _road_nodes_cache

    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nodes_file = os.path.join(data_dir, 'data', 'beijing_road_nodes.json')

    _road_nodes_cache = []
    if os.path.exists(nodes_file):
        with open(nodes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _road_nodes_cache = data.get('nodes', [])
    return _road_nodes_cache


def calc_straight_distance(x1, y1, x2, y2):
    """计算两点间直线距离（米）"""
    R = 6371000
    lat1, lon1 = math.radians(y1), math.radians(x1)
    lat2, lon2 = math.radians(y2), math.radians(x2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def find_nearest_road_node(x, y):
    """根据坐标找到最近的道路节点ID"""
    nodes = get_road_nodes()
    if not nodes:
        return None

    nearest = None
    min_dist = float('inf')
    for node in nodes:
        dist = calc_straight_distance(x, y, node.get('x', 0), node.get('y', 0))
        if dist < min_dist:
            min_dist = dist
            nearest = node.get('id')

    return nearest


def calculate_road_distance(graph, from_node_id, to_node_id):
    """使用Dijkstra计算两个道路节点间的道路距离"""
    if not from_node_id or not to_node_id:
        return float('inf')

    if from_node_id == to_node_id:
        return 0

    result = dijkstra(graph, from_node_id, to_node_id, weight='distance')
    return result.get('distance', float('inf'))


@food_bp.route('/foods', methods=['GET'])
def get_foods():
    """
    获取美食列表

    查询参数:
        campus_id: 校区ID
        cuisine: 菜系
        sort: 排序方式 heat/rating/distance
        origin: 参考点坐标，格式 "x,y"
        origin_node_id: 参考点道路节点ID（优先使用）
        limit: 返回数量
        offset: 偏移量
    """
    campus_id = request.args.get('campus_id')
    cuisine = request.args.get('cuisine')
    sort_by = request.args.get('sort', 'heat')
    origin = request.args.get('origin')  # 格式 "x,y"
    origin_node_id = request.args.get('origin_node_id')
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get('offset', 0))

    loader = get_loader()
    foods = loader.get_all_foods()

    # 按校区过滤
    if campus_id:
        foods = [f for f in foods if f.campus_id == campus_id]

    # 按菜系过滤
    if cuisine:
        foods = [f for f in foods if f.cuisine == cuisine]

    # 解析起点位置
    ref_x, ref_y = 0, 0
    if origin_node_id:
        pass
    elif origin:
        try:
            parts = origin.split(',')
            ref_x, ref_y = float(parts[0]), float(parts[1])
        except:
            return jsonify({'code': 400, 'message': 'origin格式错误，应为"x,y"', 'data': None})

    # 按距离排序
    if sort_by == 'distance':
        graph = get_road_graph()

        # 确定起点节点ID
        start_node_id = origin_node_id
        if not start_node_id and origin:
            start_node_id = find_nearest_road_node(ref_x, ref_y)

        # 计算每个美食的道路距离
        if start_node_id:
            for f in foods:
                food_node_id = getattr(f, 'location_node_id', None)
                if food_node_id:
                    f.distance = calculate_road_distance(graph, start_node_id, food_node_id)
                else:
                    f.distance = calc_straight_distance(ref_x, ref_y, f.x, f.y)
        else:
            for f in foods:
                f.distance = float('inf')

        foods = sorted(foods, key=lambda x: x.distance if hasattr(x, 'distance') and x.distance is not None else float('inf'))
    elif sort_by == 'rating':
        foods = top_k(foods, len(foods), key=lambda x: x.rating, reverse=True)
    else:  # 默认按热度
        foods = top_k(foods, len(foods), key=lambda x: x.heat, reverse=True)

    total = len(foods)
    foods = foods[offset:offset + limit]

    return jsonify({
        'code': 200,
        'data': {
            'items': [f.to_dict() for f in foods],
            'total': total,
            'limit': limit,
            'offset': offset
        },
        'message': 'success'
    })


@food_bp.route('/foods/search', methods=['GET'])
def search_foods():
    """
    搜索美食

    查询参数:
        q: 搜索关键词
        campus_id: 校区ID
        cuisine: 菜系过滤
        limit: 返回数量
    """
    query = request.args.get('q', '').strip()
    campus_id = request.args.get('campus_id')
    cuisine = request.args.get('cuisine')
    limit = int(request.args.get('limit', 10))

    loader = get_loader()
    foods = loader.get_all_foods()

    # 按校区过滤
    if campus_id:
        foods = [f for f in foods if f.campus_id == campus_id]

    # 按菜系过滤
    if cuisine:
        foods = [f for f in foods if f.cuisine == cuisine]

    # 转换为字典
    items = [f.to_dict() for f in foods]

    if not query:
        # 无搜索词，返回按热度排序的结果
        items = top_k(items, len(items), key=lambda x: x.get('heat', 0), reverse=True)
        return jsonify({
            'code': 200,
            'data': {
                'items': items[:limit],
                'total': len(items),
                'query': ''
            },
            'message': 'success'
        })

    # 模糊搜索
    results = fuzzy_search(items, query, fields=['name', 'cuisine', 'restaurant'], limit=limit)

    return jsonify({
        'code': 200,
        'data': {
            'items': results,
            'total': len(results),
            'query': query
        },
        'message': 'success'
    })


@food_bp.route('/foods/recommend', methods=['GET'])
def recommend_foods():
    """
    美食推荐

    查询参数:
        campus_id: 校区ID
        user_id: 用户ID（可选）
        limit: 返回数量
    """
    campus_id = request.args.get('campus_id')
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))

    loader = get_loader()
    foods = loader.get_all_foods()

    # 按校区过滤
    if campus_id:
        foods = [f for f in foods if f.campus_id == campus_id]

    # 如果有用户，根据用户之前喜欢的菜系推荐
    if user_id:
        user = loader.get_user(user_id)
        if user and user.interests:
            # 简单实现：用户兴趣作为菜系推荐
            recommended = []
            others = []
            for f in foods:
                if f.cuisine in user.interests:
                    recommended.append(f)
                else:
                    others.append(f)

            # 推荐排前面，按热度排序
            recommended = top_k(recommended, len(recommended), key=lambda x: x.heat, reverse=True)
            others = top_k(others, len(others), key=lambda x: x.heat, reverse=True)

            foods = recommended + others
        else:
            foods = top_k(foods, len(foods), key=lambda x: x.heat, reverse=True)
    else:
        foods = top_k(foods, len(foods), key=lambda x: x.heat, reverse=True)

    return jsonify({
        'code': 200,
        'data': {
            'items': [f.to_dict() for f in foods[:limit]],
            'total': len(foods[:limit])
        },
        'message': 'success'
    })


@food_bp.route('/cuisines', methods=['GET'])
def get_cuisines():
    """获取所有菜系"""
    from backend.models.food import Food
    return jsonify({
        'code': 200,
        'data': {
            'cuisines': Food.CUISINES
        },
        'message': 'success'
    })
