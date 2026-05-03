"""
场所查询路由 - 附近设施查找
"""

import sys
import os
import math
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from flask import Blueprint, request, jsonify

from backend.data import get_loader
from backend.core import Graph
from backend.algorithms import dijkstra
from backend.algorithms import fuzzy_search

nearby_bp = Blueprint('nearby', __name__)

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


@nearby_bp.route('/nearby', methods=['GET'])
def get_nearby():
    """
    查找附近的设施（使用道路网络距离）

    查询参数:
        origin: 参考点坐标，格式 "x,y"
        origin_node_id: 参考点道路节点ID（优先使用）
        range: 范围（米），默认500
        type: 设施类型（可选）
        category: 设施类别（可选，用于POI筛选）
        campus_id: 校区ID
        limit: 返回数量
    """
    origin = request.args.get('origin')  # 格式 "x,y"
    origin_node_id = request.args.get('origin_node_id')
    search_range = float(request.args.get('range', 500))
    facility_type = request.args.get('type')
    category = request.args.get('category')
    campus_id = request.args.get('campus_id')
    limit = int(request.args.get('limit', 10))

    loader = get_loader()
    facilities = loader.get_all_facilities()

    # 按校区过滤
    if campus_id:
        facilities = [f for f in facilities if f.campus_id == campus_id]

    # 按类型过滤（兼容type和category参数）
    if facility_type:
        facilities = [f for f in facilities if f.type == facility_type]
    elif category:
        facilities = [f for f in facilities if f.type == category]

    # 解析起点位置
    ref_x, ref_y = 0, 0
    if origin_node_id:
        # 直接使用节点ID
        pass
    elif origin:
        # 从坐标查找最近节点
        try:
            parts = origin.split(',')
            ref_x, ref_y = float(parts[0]), float(parts[1])
        except:
            return jsonify({'code': 400, 'message': 'origin格式错误，应为"x,y"', 'data': None})

    # 获取道路网络图
    graph = get_road_graph()

    # 确定起点节点ID
    start_node_id = origin_node_id
    if not start_node_id and origin:
        start_node_id = find_nearest_road_node(ref_x, ref_y)

    # 计算每个设施的道路距离并过滤
    nearby_facilities = []
    for f in facilities:
        facility_node_id = getattr(f, 'location_node_id', None)

        if not facility_node_id:
            # 如果设施没有挂载到道路网络，跳过
            continue

        # 计算道路距离
        if start_node_id:
            dist = calculate_road_distance(graph, start_node_id, facility_node_id)
        else:
            # 如果没有起点，使用直线距离
            dist = calc_straight_distance(ref_x, ref_y, f.x, f.y)

        if dist <= search_range:
            f.distance = dist
            nearby_facilities.append(f)

    # 按道路距离排序
    nearby_items = [f.to_dict() for f in nearby_facilities]
    nearby_items = sorted(nearby_items, key=lambda f: f.get('distance', float('inf')))

    return jsonify({
        'code': 200,
        'data': {
            'items': nearby_items[:limit],
            'total': len(nearby_items),
            'reference': {
                'origin': origin,
                'origin_node_id': start_node_id,
                'range': search_range
            }
        },
        'message': 'success'
    })


@nearby_bp.route('/facilities', methods=['GET'])
def get_facilities():
    """
    获取设施列表

    查询参数:
        campus_id: 校区ID
        type: 设施类型
    """
    campus_id = request.args.get('campus_id')
    facility_type = request.args.get('type')

    loader = get_loader()
    facilities = loader.get_all_facilities()

    # 按校区过滤
    if campus_id:
        facilities = [f for f in facilities if f.campus_id == campus_id]

    # 按类型过滤
    if facility_type:
        facilities = [f for f in facilities if f.type == facility_type]

    return jsonify({
        'code': 200,
        'data': {
            'items': [f.to_dict() for f in facilities],
            'total': len(facilities),
            'types': loader.get_facilities_by_type(facility_type) if facility_type else []
        },
        'message': 'success'
    })


@nearby_bp.route('/facilities/search', methods=['GET'])
def search_facilities():
    """
    搜索设施

    查询参数:
        q: 搜索关键词
        campus_id: 校区ID
        limit: 返回数量
    """
    query = request.args.get('q', '').strip()
    campus_id = request.args.get('campus_id')
    limit = int(request.args.get('limit', 10))

    if not query:
        return jsonify({
            'code': 200,
            'data': {'items': [], 'total': 0},
            'message': 'success'
        })

    loader = get_loader()
    facilities = loader.get_all_facilities()

    # 按校区过滤
    if campus_id:
        facilities = [f for f in facilities if f.campus_id == campus_id]

    # 转换为字典
    items = [f.to_dict() for f in facilities]

    # 模糊搜索
    results = fuzzy_search(items, query, fields=['name', 'type'], limit=limit)

    return jsonify({
        'code': 200,
        'data': {
            'items': results,
            'total': len(results),
            'query': query
        },
        'message': 'success'
    })


@nearby_bp.route('/facility-types', methods=['GET'])
def get_facility_types():
    """获取所有设施类型"""
    from backend.models.facility import Facility
    return jsonify({
        'code': 200,
        'data': {
            'types': Facility.FACILITY_TYPES
        },
        'message': 'success'
    })
