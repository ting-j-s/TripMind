"""
路线路由 - 最短路径、TSP路线规划
"""

import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, jsonify

from backend.data import get_loader
from backend.algorithms import dijkstra, dijkstra_with_constraints, solve_tsp, get_route_info

route_bp = Blueprint('route', __name__)

# 景点ID到图节点ID的缓存
_attraction_node_cache = {}
# 道路节点坐标缓存
_road_nodes_cache = None


def get_road_nodes():
    """获取所有道路节点的坐标"""
    global _road_nodes_cache
    if _road_nodes_cache is None:
        _road_nodes_cache = []
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        nodes_file = os.path.join(data_dir, 'data', 'beijing_road_nodes.json')
        if os.path.exists(nodes_file):
            import json
            with open(nodes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _road_nodes_cache = data.get('nodes', [])
    return _road_nodes_cache


def calc_distance(x1, y1, x2, y2):
    """计算两点间距离（米）"""
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2) * 111000  # 约111km per degree


def find_nearest_road_node(x, y):
    """根据坐标找到最近的道路节点ID"""
    nodes = get_road_nodes()
    if not nodes:
        return None

    nearest = None
    min_dist = float('inf')
    for node in nodes:
        dist = calc_distance(x, y, node.get('x', 0), node.get('y', 0))
        if dist < min_dist:
            min_dist = dist
            nearest = node.get('id')

    return nearest


def resolve_location_id(location_id, loader):
    """
    将景点/位置ID解析为图节点ID

    支持格式:
    - 景点ID: ATTR_BJ_xxx -> 找到最近的BJ_NODE_xxx
    - 校园ID: BUPT -> 使用校园作为节点
    - 建筑ID: BUPT_xxx -> 直接使用
    - 图节点ID: BJ_NODE_xxx -> 直接返回
    """
    global _attraction_node_cache

    if not location_id:
        return None

    # 如果已经是图节点ID，直接返回
    if location_id.startswith('BJ_NODE_'):
        return location_id

    # 如果是建筑ID（BUPT_xxx格式），直接返回
    if location_id.startswith('BUPT_') or location_id.startswith('FAC_'):
        return location_id

    # 检查缓存
    if location_id in _attraction_node_cache:
        return _attraction_node_cache[location_id]

    # 尝试作为景点ID处理
    attraction = loader.get_attraction(location_id)
    if attraction:
        # 找到最近的图节点
        nearest = find_nearest_road_node(attraction.x, attraction.y)
        if nearest:
            _attraction_node_cache[location_id] = nearest
            return nearest

    # 如果是校园ID，使用校园坐标找最近节点
    campus = loader.get_campus(location_id)
    if campus:
        nearest = find_nearest_road_node(campus.x, campus.y)
        if nearest:
            _attraction_node_cache[location_id] = nearest
            return nearest

    return None


@route_bp.route('/shortest', methods=['POST'])
def shortest_path():
    """
    最短路径规划

    请求:
        {
            "from": "起点节点ID",
            "to": "终点节点ID",
            "campus_id": "校区ID",
            "transport": "交通方式",  // 步行/自行车/电瓶车
            "weight": "distance" 或 "time"
        }

    返回:
        {
            "code": 200,
            "data": {
                "path": ["A", "B", "C"],
                "distance": 150,
                "time": 180,
                "segments": [...]
            }
        }
    """
    data = request.get_json()
    from_id = data.get('from')  # 原始ID（可能是景点ID）
    to_id = data.get('to')      # 原始ID（可能是景点ID）
    campus_id = data.get('campus_id')
    transport = data.get('transport', '步行')
    weight = data.get('weight', 'distance')

    if not from_id or not to_id:
        return jsonify({'code': 400, 'message': '起点和终点不能为空', 'data': None})

    loader = get_loader()
    graph = loader.get_graph(campus_id)

    # 将景点ID转换为图节点ID
    from_node = resolve_location_id(from_id, loader)
    to_node = resolve_location_id(to_id, loader)

    # 获取景点名称用于显示
    from_attr = loader.get_attraction(from_id)
    to_attr = loader.get_attraction(to_id)
    from_name = from_attr.name if from_attr else (loader.get_campus(from_id).name if loader.get_campus(from_id) else from_id)
    to_name = to_attr.name if to_attr else (loader.get_campus(to_id).name if loader.get_campus(to_id) else to_id)

    # 检查节点是否存在
    if not from_node:
        return jsonify({'code': 404, 'message': f'起点{from_id}无法映射到有效节点', 'data': None})

    if not to_node:
        return jsonify({'code': 404, 'message': f'终点{to_id}无法映射到有效节点', 'data': None})

    if not graph.node_exists(from_node):
        return jsonify({'code': 404, 'message': f'起点节点{from_node}不存在', 'data': None})

    if not graph.node_exists(to_node):
        return jsonify({'code': 404, 'message': f'终点节点{to_node}不存在', 'data': None})

    # 如果选择了交通工具约束
    if transport != '步行':
        result = dijkstra_with_constraints(graph, from_node, to_node,
                                          transport=transport, weight=weight)
        if not result.get('success'):
            return jsonify({'code': 404, 'message': '无可用路径', 'data': None})

        path = result['path']
        distance = result.get('distance', 0)
        time = result.get('time', 0)
    else:
        # 普通最短路径
        result = dijkstra(graph, from_node, to_node, weight=weight)
        path = result.get('path', [])
        distance = result.get('distance', 0)

        # 获取路径详情（用于时间计算）
        if path:
            path_info = get_route_info(graph, path, weight=weight, transport=transport)
            time = path_info['total_time']
        else:
            return jsonify({'code': 404, 'message': '无法找到路径', 'data': None})

    if not path:
        return jsonify({'code': 404, 'message': '无法找到路径', 'data': None})

    # 获取节点名称和坐标映射
    nodes_info = get_road_nodes()
    node_name_map = {n['id']: n.get('name', n['id']) for n in nodes_info}
    node_coord_map = {n['id']: {'x': n.get('x', 0), 'y': n.get('y', 0)} for n in nodes_info}

    # 构建path坐标列表（用于前端可视化）
    path_coords = []
    for node_id in path:
        # 如果是景点节点ID，尝试找对应坐标
        if node_id.startswith('ATTR_') or node_id.startswith('BUPT'):
            attr = loader.get_attraction(node_id)
            if attr:
                path_coords.append({'id': node_id, 'x': attr.x, 'y': attr.y, 'name': attr.name})
            else:
                campus = loader.get_campus(node_id)
                if campus:
                    path_coords.append({'id': node_id, 'x': campus.x, 'y': campus.y, 'name': campus.name})
                else:
                    path_coords.append({'id': node_id, 'x': 0, 'y': 0, 'name': node_id})
        else:
            # 图节点，直接用坐标
            coord = node_coord_map.get(node_id, {'x': 0, 'y': 0})
            path_coords.append({
                'id': node_id,
                'x': coord['x'],
                'y': coord['y'],
                'name': node_name_map.get(node_id, node_id)
            })

    # 构建path_names用于显示
    path_names = []
    for node_id in path:
        path_names.append(node_name_map.get(node_id, node_id))

    # 替换起终点名称
    if path_names and len(path_names) >= 2:
        path_names[0] = from_name
        path_names[-1] = to_name

    # 更新起终点坐标
    if path_coords:
        if len(path_coords) >= 1:
            path_coords[0]['name'] = from_name
            from_attr = loader.get_attraction(from_id)
            if from_attr:
                path_coords[0]['x'] = from_attr.x
                path_coords[0]['y'] = from_attr.y
        if len(path_coords) >= 2:
            path_coords[-1]['name'] = to_name
            to_attr = loader.get_attraction(to_id)
            if to_attr:
                path_coords[-1]['x'] = to_attr.x
                path_coords[-1]['y'] = to_attr.y

    return jsonify({
        'code': 200,
        'data': {
            'path': path,
            'path_names': path_names,
            'path_coords': path_coords,
            'from_name': from_name,
            'to_name': to_name,
            'from_node': from_node,
            'to_node': to_node,
            'distance': distance,
            'time': time,
            'segments': path_info.get('segments', [])
        },
        'message': 'success'
    })


@route_bp.route('/tsp', methods=['POST'])
def tsp_route():
    """
    TSP多景点路线规划

    请求:
        {
            "start": "起点ID(景点ID或节点ID)",
            "nodes": ["节点1", "节点2", "节点3"],  // 景点ID列表
            "campus_id": "校区ID",
            "transport": "交通方式",
            "optimize": true  // 是否2-opt优化
        }

    返回:
        {
            "code": 200,
            "data": {
                "path": ["起点", "A", "B", "C", "起点"],
                "path_names": ["故宫", "天坛", "颐和园"],
                "visited_order": ["ATTR_BJ_001", "ATTR_BJ_003", "ATTR_BJ_004"],
                "total_distance": 500,
                "total_time": 600
            }
        }
    """
    data = request.get_json()
    start_id = data.get('start')
    node_ids = data.get('nodes', [])  # 原始景点ID列表
    campus_id = data.get('campus_id')
    transport = data.get('transport', '步行')
    optimize = data.get('optimize', True)

    if not start_id:
        return jsonify({'code': 400, 'message': '起点不能为空', 'data': None})

    if len(node_ids) < 1:
        return jsonify({'code': 400, 'message': '至少需要一个目标节点', 'data': None})

    loader = get_loader()

    # 将景点ID转换为图节点ID
    start_node = resolve_location_id(start_id, loader)
    if not start_node:
        return jsonify({'code': 404, 'message': f'起点{start_id}无法映射到有效节点', 'data': None})

    # 转换所有目标节点
    target_nodes = []
    for node_id in node_ids:
        mapped = resolve_location_id(node_id, loader)
        if mapped:
            target_nodes.append(mapped)

    if len(target_nodes) < 1:
        return jsonify({'code': 404, 'message': '所有目标节点都无法映射', 'data': None})

    graph = loader.get_graph(campus_id)

    # 检查节点是否存在
    if not graph.node_exists(start_node):
        return jsonify({'code': 404, 'message': f'起点节点{start_node}不存在', 'data': None})

    for node in target_nodes:
        if not graph.node_exists(node):
            return jsonify({'code': 404, 'message': f'节点{node}不存在', 'data': None})

    # 求解TSP
    result = solve_tsp(graph, start_node, target_nodes, optimize=optimize)

    if not result.get('success', False):
        return jsonify({'code': 404, 'message': result.get('error', '无法找到可行路线'), 'data': None})

    # 获取节点名称映射
    nodes_info = get_road_nodes()
    node_name_map = {n['id']: n.get('name', n['id']) for n in nodes_info}

    # 构建path_names
    path = result.get('path', [])
    path_names = []
    for node_id in path:
        path_names.append(node_name_map.get(node_id, node_id))

    # 替换起点名称
    if path_names:
        start_attr = loader.get_attraction(start_id)
        start_name = start_attr.name if start_attr else (loader.get_campus(start_id).name if loader.get_campus(start_id) else start_id)
        path_names[0] = start_name

    # 构建景点名称列表（用于显示）
    visited_names = []
    visited_order = result.get('visited_order', [])
    for node_id in visited_order:
        # 反向查找景点ID
        attr_name = node_name_map.get(node_id, node_id)
        # 检查是否是映射的景点
        for orig_id in node_ids:
            mapped = resolve_location_id(orig_id, loader)
            if mapped == node_id:
                attr = loader.get_attraction(orig_id)
                if attr:
                    attr_name = attr.name
                    break
        visited_names.append(attr_name)

    return jsonify({
        'code': 200,
        'data': {
            'path': path,
            'path_names': path_names,
            'visited_order': visited_order,
            'visited_names': visited_names,
            'total_distance': result.get('total_distance', 0),
            'total_time': result.get('total_time', 0)
        },
        'message': 'success'
    })


@route_bp.route('/indoor', methods=['POST'])
def indoor_route():
    """
    室内导航

    请求:
        {
            "building_id": "建筑ID",
            "start": "起点位置",  // gate/entrance/elevator/room_id/节点ID
            "end": "终点位置",     // room_id/elevator/节点ID
            "strategy": "time" 或 "distance"
        }

    返回:
        {
            "code": 200,
            "data": {
                "success": true,
                "building_id": "BLD_001",
                "building_name": "教学楼A",
                "start": "gate",
                "end": "room_301",
                "strategy": "time",
                "path": ["node1", "node2", ...],
                "path_nodes": [{node_id, name, floor, type}, ...],
                "total_distance": 95,
                "total_time": 82,
                "algorithm": "Dijkstra on indoor graph"
            }
        }
    """
    data = request.get_json()
    building_id = data.get('building_id')
    start = data.get('start')
    end = data.get('end')
    strategy = data.get('strategy', 'time')

    if not building_id:
        return jsonify({'code': 400, 'message': 'building_id不能为空', 'data': None})

    if not start:
        return jsonify({'code': 400, 'message': '起点(start)不能为空', 'data': None})

    if not end:
        return jsonify({'code': 400, 'message': '终点(end)不能为空', 'data': None})

    # 使用室内导航服务
    from backend.services.indoor_navigation_service import plan_indoor_route

    result = plan_indoor_route(building_id, start, end, strategy)

    if result.get('success'):
        return jsonify({
            'code': 200,
            'data': result,
            'message': 'success'
        })
    else:
        return jsonify({
            'code': 404,
            'data': result,
            'message': result.get('message', '室内导航失败')
        })
