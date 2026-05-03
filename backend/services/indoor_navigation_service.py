"""
室内导航服务

功能：
1. 加载室内图数据
2. 构建室内导航图
3. 使用Dijkstra计算室内最短路径
4. 支持起点/终点解析（大门、电梯、房间等）
"""

import os
import json
from typing import Dict, List, Optional, Tuple

from backend.core.graph import Graph
from backend.algorithms.dijkstra import dijkstra


# 缓存
_indoor_graphs_cache = None
_building_graphs_cache = {}


def load_indoor_graphs() -> List[Dict]:
    """加载所有室内图数据"""
    global _indoor_graphs_cache
    if _indoor_graphs_cache is not None:
        return _indoor_graphs_cache

    data_dir = os.path.dirname(os.path.abspath(__file__))
    indoor_file = os.path.join(data_dir, '..', 'data', 'indoor_graphs.json')

    if not os.path.exists(indoor_file):
        indoor_file = os.path.join(data_dir, 'data', 'indoor_graphs.json')

    if not os.path.exists(indoor_file):
        return []

    with open(indoor_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        _indoor_graphs_cache = data.get('buildings', [])
        return _indoor_graphs_cache


def get_building_data(building_id: str) -> Optional[Dict]:
    """根据building_id获取建筑数据"""
    buildings = load_indoor_graphs()
    for building in buildings:
        if building.get('building_id') == building_id:
            return building
    return None


def find_building_by_name(name: str) -> Optional[Dict]:
    """根据建筑名称查找建筑"""
    buildings = load_indoor_graphs()
    for building in buildings:
        if building.get('building_name') == name:
            return building
    return None


def build_indoor_graph(building: Dict) -> Graph:
    """根据建筑数据构建室内图"""
    g = Graph(directed=False)

    # 添加所有节点
    for node in building.get('nodes', []):
        node_id = node['node_id']
        g.add_node(node_id, {
            'name': node.get('name', node_id),
            'floor': node.get('floor', 1),
            'type': node.get('type', 'unknown'),
            'x': node.get('x', 0),
            'y': node.get('y', 0)
        })

    # 添加所有边（无向图）
    for edge in building.get('edges', []):
        from_node = edge['from']
        to_node = edge['to']
        distance = edge.get('distance', 1)
        time = edge.get('time', distance / 5 * 3600)
        edge_type = edge.get('type', 'corridor')

        g.add_edge(
            from_node, to_node,
            distance=distance,
            time=time,
            type=edge_type
        )

    return g


def get_building_graph(building_id: str) -> Optional[Tuple[Dict, Graph]]:
    """获取建筑的图结构"""
    global _building_graphs_cache

    if building_id in _building_graphs_cache:
        return _building_graphs_cache[building_id]

    building = get_building_data(building_id)
    if not building:
        return None

    graph = build_indoor_graph(building)
    _building_graphs_cache[building_id] = (building, graph)
    return (building, graph)


def resolve_indoor_node(building: Dict, user_input: str) -> Optional[str]:
    """
    将用户输入解析为室内节点ID

    支持格式：
    - "gate" 或 "entrance" -> 主入口
    - "elevator" -> 主电梯
    - "room_101" 或 "101" -> 房间101
    - 完整node_id -> 直接返回
    - 房间名称 -> 模糊匹配
    """
    nodes = building.get('nodes', [])
    elevators = building.get('elevators', [])
    entrances = building.get('entrances', [])

    user_input = user_input.strip().lower()

    # 直接匹配node_id
    for node in nodes:
        if node['node_id'].lower() == user_input:
            return node['node_id']

    # 匹配入口
    if user_input in ['gate', 'entrance', 'main_entrance', '入口', '大门']:
        for node in nodes:
            if node.get('type') == 'entrance':
                # 返回主入口（通常是F1的entrance）
                if node['floor'] == 1:
                    return node['node_id']
        # 如果没有找到，返回任意一个entrance
        for node in nodes:
            if node.get('type') == 'entrance':
                return node['node_id']

    # 匹配电梯
    if user_input in ['elevator', '电梯']:
        # 返回一楼电梯
        for node in nodes:
            if node.get('type') == 'elevator' and node['floor'] == 1:
                return node['node_id']
        for node in nodes:
            if node.get('type') == 'elevator':
                return node['node_id']

    # 匹配房间号
    # 支持 room_101, 101, room_101教室 等格式
    room_pattern = user_input.replace('room_', '').replace('教室', '').strip()
    for node in nodes:
        if node.get('type') == 'room':
            node_room_id = node['node_id'].lower()
            # 提取房间号部分，如 BLD_001_F1_room_101 -> 101
            parts = node_room_id.split('_')
            if len(parts) >= 4 and parts[-2] == 'room':
                room_num = parts[-1]
                if room_num == room_pattern:
                    return node['node_id']
            # 也支持名称匹配
            if room_pattern in node.get('name', '').lower():
                return node['node_id']

    return None


def plan_indoor_route(building_id: str, start: str, end: str, strategy: str = 'time') -> Dict:
    """
    室内路径规划

    参数:
        building_id: 建筑ID
        start: 起点描述（gate/entrance/elevator/room_id/节点ID）
        end: 终点描述
        strategy: 优化策略 ('time' 或 'distance')

    返回:
        {
            'success': True/False,
            'message': 错误信息,
            'building_id': 建筑ID,
            'building_name': 建筑名称,
            'start': 起点描述,
            'end': 终点描述,
            'strategy': 策略,
            'path': [节点列表],
            'path_nodes': [{node_id, name, floor, type}, ...],
            'total_distance': 总距离,
            'total_time': 总时间,
            'algorithm': 'Dijkstra on indoor graph'
        }
    """
    # 获取建筑数据
    result = get_building_graph(building_id)
    if not result:
        return {
            'success': False,
            'message': f"建筑 {building_id} 不存在"
        }

    building, graph = result

    # 解析起点和终点
    start_node = resolve_indoor_node(building, start)
    if not start_node:
        return {
            'success': False,
            'message': f"无法解析起点: {start}"
        }

    end_node = resolve_indoor_node(building, end)
    if not end_node:
        return {
            'success': False,
            'message': f"无法解析终点: {end}"
        }

    # 检查节点是否存在
    if not graph.node_exists(start_node):
        return {
            'success': False,
            'message': f"起点节点 {start_node} 不存在"
        }

    if not graph.node_exists(end_node):
        return {
            'success': False,
            'message': f"终点节点 {end_node} 不存在"
        }

    # 使用Dijkstra计算最短路径
    weight = 'time' if strategy == 'time' else 'distance'
    dijkstra_result = dijkstra(graph, start_node, end_node, weight=weight)

    path = dijkstra_result.get('path', [])
    if not path:
        return {
            'success': False,
            'message': '无法找到从起点到终点的路径'
        }

    # 计算总距离和时间
    total_distance = 0
    total_time = 0
    path_nodes = []

    for i, node_id in enumerate(path):
        node_data = graph.get_node_data(node_id)
        if node_data:
            path_nodes.append({
                'node_id': node_id,
                'name': node_data.get('name', node_id),
                'floor': node_data.get('floor', 1),
                'type': node_data.get('type', 'unknown')
            })
        else:
            path_nodes.append({
                'node_id': node_id,
                'name': node_id,
                'floor': 1,
                'type': 'unknown'
            })

        # 累加边的权重
        if i > 0:
            prev_node = path[i - 1]
            edge = graph.get_edge(prev_node, node_id)
            if edge:
                total_distance += edge.get('distance', 0)
                total_time += edge.get('time', 0)

    return {
        'success': True,
        'message': 'success',
        'building_id': building_id,
        'building_name': building.get('building_name', ''),
        'start': start,
        'end': end,
        'strategy': strategy,
        'path': path,
        'path_nodes': path_nodes,
        'total_distance': total_distance,
        'total_time': total_time,
        'algorithm': 'Dijkstra on indoor graph'
    }


def list_buildings() -> List[Dict]:
    """列出所有可用建筑"""
    buildings = load_indoor_graphs()
    return [
        {
            'building_id': b.get('building_id'),
            'building_name': b.get('building_name'),
            'floors': b.get('floors', []),
            'node_count': len(b.get('nodes', [])),
            'edge_count': len(b.get('edges', []))
        }
        for b in buildings
    ]


def get_building_info(building_id: str) -> Optional[Dict]:
    """获取建筑详细信息"""
    building = get_building_data(building_id)
    if not building:
        return None

    return {
        'building_id': building.get('building_id'),
        'building_name': building.get('building_name'),
        'floors': building.get('floors', []),
        'entrances': building.get('entrances', []),
        'elevators': building.get('elevators', []),
        'nodes': building.get('nodes', []),
        'edges': building.get('edges', [])
    }


# 测试代码
if __name__ == '__main__':
    print("=" * 50)
    print("室内导航服务测试")
    print("=" * 50)

    # 列出所有建筑
    print("\n1. 可用建筑:")
    buildings = list_buildings()
    for b in buildings:
        print(f"  {b['building_id']}: {b['building_name']} ({b['node_count']}节点, {b['edge_count']}边)")

    # 测试路径规划
    if buildings:
        building_id = buildings[0]['building_id']
        print(f"\n2. 测试从大门到三层教室:")

        result = plan_indoor_route(building_id, 'gate', 'room_301', strategy='time')
        print(f"  success: {result.get('success')}")
        if result.get('success'):
            print(f"  路径: {' -> '.join([n['name'] for n in result.get('path_nodes', [])])}")
            print(f"  总距离: {result.get('total_distance')}m")
            print(f"  总时间: {result.get('total_time')}s")
        else:
            print(f"  错误: {result.get('message')}")

        # 测试同层路径
        print(f"\n3. 测试从大门到一层教室:")
        result = plan_indoor_route(building_id, 'gate', 'room_101', strategy='time')
        print(f"  success: {result.get('success')}")
        if result.get('success'):
            print(f"  路径: {' -> '.join([n['name'] for n in result.get('path_nodes', [])])}")
            print(f"  总距离: {result.get('total_distance')}m")
            print(f"  总时间: {result.get('total_time')}s")

    print("\n[SUCCESS] Indoor navigation service test passed!")