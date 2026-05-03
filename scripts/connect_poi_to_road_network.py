"""
道路网络构建与POI挂载脚本

功能：
1. 从现有数据文件加载道路网络
2. 构建Graph并找最大连通分量
3. 将所有POI挂载到有效道路节点
4. 修复location_node_id字段
"""

import os
import sys
import json
import math
from collections import deque

# 添加backend路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.graph import Graph


def calc_distance(x1, y1, x2, y2):
    """计算两点间直线距离（米），用于找最近节点"""
    R = 6371000  # 地球半径（米）
    lat1, lon1 = math.radians(y1), math.radians(x1)
    lat2, lon2 = math.radians(y2), math.radians(x2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def load_road_network():
    """加载道路网络数据，返回nodes和edges"""
    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    nodes = {}  # node_id -> {x, y}
    edges = []

    # 优先加载roads.json（格式最标准）
    roads_file = os.path.join(data_dir, 'roads.json')
    if os.path.exists(roads_file):
        with open(roads_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for road in data.get('roads', []):
                from_node = road['from']
                to_node = road['to']

                # 记录边
                edges.append({
                    'id': road['id'],
                    'from': from_node,
                    'to': to_node,
                    'distance': road['distance'],
                    'ideal_speed': road.get('ideal_speed', 30),
                    'congestion': road.get('congestion', 1.0),
                    'road_types': road.get('road_types', ['步行'])
                })

    # 加载beijing_road_nodes.json获取节点坐标
    nodes_file = os.path.join(data_dir, 'beijing_road_nodes.json')
    if os.path.exists(nodes_file):
        with open(nodes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for node in data.get('nodes', []):
                nodes[node['id']] = {
                    'x': node['x'],
                    'y': node['y']
                }

    # 补充beijing_roads_real.json中的节点
    real_roads_file = os.path.join(data_dir, 'beijing_roads_real.json')
    if os.path.exists(real_roads_file):
        with open(real_roads_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for road in data.get('roads', []):
                from_node = road['from']
                to_node = road['to']
                # 添加节点坐标（如果有）
                if 'from_lat' in road and 'from_lon' in road:
                    nodes[from_node] = {'x': road['from_lon'], 'y': road['from_lat']}
                if 'to_lat' in road and 'to_lon' in road:
                    nodes[to_node] = {'x': road['to_lon'], 'y': road['to_lat']}

    return nodes, edges


def build_graph(nodes, edges):
    """从nodes和edges构建Graph"""
    g = Graph(directed=False)

    # 添加所有节点
    for node_id, coord in nodes.items():
        g.add_node(node_id, {'x': coord['x'], 'y': coord['y']})

    # 添加所有边
    for edge in edges:
        g.add_edge(
            edge['from'],
            edge['to'],
            distance=edge['distance'],
            time=edge['distance'] / edge['ideal_speed'] * 3.6 if edge['ideal_speed'] > 0 else 0,
            ideal_speed=edge['ideal_speed'],
            congestion=edge['congestion'],
            road_types=edge['road_types']
        )

    return g


def find_largest_connected_component(graph):
    """使用BFS找最大连通分量"""
    all_nodes = graph.get_all_nodes()
    visited = set()
    largest_cc = set()

    for start_node in all_nodes:
        if start_node in visited:
            continue

        # BFS
        component = set()
        queue = deque([start_node])
        visited.add(start_node)

        while queue:
            node = queue.popleft()
            component.add(node)

            for neighbor_info in graph.get_neighbors(node):
                neighbor = neighbor_info['node']
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        if len(component) > len(largest_cc):
            largest_cc = component

    return largest_cc


def find_nearest_node(x, y, nodes, valid_nodes):
    """找最近的有效节点（基于直线距离）"""
    if not valid_nodes:
        return None

    nearest = None
    min_dist = float('inf')

    for node_id in valid_nodes:
        if node_id not in nodes:
            continue
        coord = nodes[node_id]
        dist = calc_distance(x, y, coord['x'], coord['y'])
        if dist < min_dist:
            min_dist = dist
            nearest = node_id

    return nearest


def stable_hash_node(poi_id, valid_nodes):
    """基于poi_id哈希稳定分配节点"""
    if not valid_nodes:
        return None

    hash_val = sum(ord(c) for c in str(poi_id))
    idx = hash_val % len(valid_nodes)
    return list(valid_nodes)[idx]


def connect_poi_to_road_network():
    """主函数：连接POI到道路网络"""
    print("=" * 60)
    print("POI道路网络挂载修复")
    print("=" * 60)

    # 1. 加载道路网络
    print("\n[1] 加载道路网络数据...")
    nodes, edges = load_road_network()
    print(f"    加载了 {len(nodes)} 个道路节点")
    print(f"    加载了 {len(edges)} 条道路边")

    # 2. 构建Graph
    print("\n[2] 构建道路图...")
    graph = build_graph(nodes, edges)
    print(f"    图节点数: {graph.node_count()}")
    print(f"    图边数: {graph.edge_count()}")

    # 3. 找最大连通分量
    print("\n[3] 查找最大连通分量...")
    largest_cc = find_largest_connected_component(graph)
    print(f"    最大连通分量节点数: {len(largest_cc)}")
    print(f"    连通分量数量: ", end="")

    all_nodes = set(graph.get_all_nodes())
    visited = set()
    cc_count = 0
    for node in all_nodes:
        if node not in visited:
            cc_count += 1
            # BFS to mark visited
            queue = deque([node])
            while queue:
                n = queue.popleft()
                if n in visited:
                    continue
                visited.add(n)
                for neighbor_info in graph.get_neighbors(n):
                    if neighbor_info['node'] not in visited:
                        queue.append(neighbor_info['node'])
    print(cc_count)

    if not largest_cc:
        print("错误：无法找到有效连通分量！")
        return False

    # 4. 修复POI数据
    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    stats = {
        'attractions': {'total': 0, 'fixed': 0, 'no_coords': 0},
        'buildings': {'total': 0, 'fixed': 0, 'no_coords': 0},
        'facilities': {'total': 0, 'fixed': 0, 'no_coords': 0},
        'foods': {'total': 0, 'fixed': 0, 'no_coords': 0}
    }

    # 4.1 修复attractions.json
    print("\n[4] 修复POI数据...")
    attractions_file = os.path.join(data_dir, 'attractions.json')
    if os.path.exists(attractions_file):
        with open(attractions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('attractions', []):
            stats['attractions']['total'] += 1
            poi_id = item.get('id', '')

            # 检查是否已有有效location_node_id
            existing_node = item.get('location_node_id')
            if existing_node and existing_node in largest_cc:
                continue  # 已有有效节点

            # 尝试用坐标找最近节点
            x, y = item.get('x', 0), item.get('y', 0)
            if x and y:
                nearest = find_nearest_node(x, y, nodes, largest_cc)
                if nearest:
                    item['location_node_id'] = nearest
                    stats['attractions']['fixed'] += 1
                else:
                    # 无法找到，分配一个稳定节点
                    item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                    stats['attractions']['fixed'] += 1
            else:
                # 没有坐标，直接哈希分配
                item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                stats['attractions']['no_coords'] += 1
                stats['attractions']['fixed'] += 1

        with open(attractions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"    attractions.json: 总数={stats['attractions']['total']}, 修复={stats['attractions']['fixed']}, 无坐标={stats['attractions']['no_coords']}")

    # 4.2 修复buildings.json
    buildings_file = os.path.join(data_dir, 'buildings.json')
    if os.path.exists(buildings_file):
        with open(buildings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('buildings', []):
            stats['buildings']['total'] += 1
            poi_id = item.get('id', '')

            existing_node = item.get('location_node_id')
            if existing_node and existing_node in largest_cc:
                continue

            x, y = item.get('x', 0), item.get('y', 0)
            if x and y:
                nearest = find_nearest_node(x, y, nodes, largest_cc)
                if nearest:
                    item['location_node_id'] = nearest
                    stats['buildings']['fixed'] += 1
                else:
                    item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                    stats['buildings']['fixed'] += 1
            else:
                item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                stats['buildings']['no_coords'] += 1
                stats['buildings']['fixed'] += 1

        with open(buildings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"    buildings.json: 总数={stats['buildings']['total']}, 修复={stats['buildings']['fixed']}, 无坐标={stats['buildings']['no_coords']}")

    # 4.3 修复facilities.json
    facilities_file = os.path.join(data_dir, 'facilities.json')
    if os.path.exists(facilities_file):
        with open(facilities_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('facilities', []):
            stats['facilities']['total'] += 1
            poi_id = item.get('id', '')

            existing_node = item.get('location_node_id')
            if existing_node and existing_node in largest_cc:
                continue

            x, y = item.get('x', 0), item.get('y', 0)
            if x and y:
                nearest = find_nearest_node(x, y, nodes, largest_cc)
                if nearest:
                    item['location_node_id'] = nearest
                    stats['facilities']['fixed'] += 1
                else:
                    item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                    stats['facilities']['fixed'] += 1
            else:
                item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                stats['facilities']['no_coords'] += 1
                stats['facilities']['fixed'] += 1

        with open(facilities_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"    facilities.json: 总数={stats['facilities']['total']}, 修复={stats['facilities']['fixed']}, 无坐标={stats['facilities']['no_coords']}")

    # 4.4 修复foods.json
    foods_file = os.path.join(data_dir, 'foods.json')
    if os.path.exists(foods_file):
        with open(foods_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('foods', []):
            stats['foods']['total'] += 1
            poi_id = item.get('id', '')

            existing_node = item.get('location_node_id')
            if existing_node and existing_node in largest_cc:
                continue

            x, y = item.get('x', 0), item.get('y', 0)
            if x and y:
                nearest = find_nearest_node(x, y, nodes, largest_cc)
                if nearest:
                    item['location_node_id'] = nearest
                    stats['foods']['fixed'] += 1
                else:
                    item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                    stats['foods']['fixed'] += 1
            else:
                item['location_node_id'] = stable_hash_node(poi_id, largest_cc)
                stats['foods']['no_coords'] += 1
                stats['foods']['fixed'] += 1

        with open(foods_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"    foods.json: 总数={stats['foods']['total']}, 修复={stats['foods']['fixed']}, 无坐标={stats['foods']['no_coords']}")

    print("\n" + "=" * 60)
    print("完成！所有POI已挂载到道路网络最大连通分量")
    print("=" * 60)

    return True


if __name__ == '__main__':
    connect_poi_to_road_network()