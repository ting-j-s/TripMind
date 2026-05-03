"""
道路网络验证脚本

功能：
1. 验证道路图结构
2. 检查连通分量
3. 验证POI可达性
4. 测试Dijkstra计算
"""

import os
import sys
import json
import math
import random
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.graph import Graph
from backend.algorithms.dijkstra import dijkstra


def calc_distance(x1, y1, x2, y2):
    """计算两点间直线距离（米）"""
    R = 6371000
    lat1, lon1 = math.radians(y1), math.radians(x1)
    lat2, lon2 = math.radians(y2), math.radians(x2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def load_road_network():
    """加载道路网络"""
    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    nodes = {}
    edges = []

    # 加载roads.json
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

    # 加载节点坐标
    nodes_file = os.path.join(data_dir, 'beijing_road_nodes.json')
    if os.path.exists(nodes_file):
        with open(nodes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for node in data.get('nodes', []):
                nodes[node['id']] = {'x': node['x'], 'y': node['y']}

    return nodes, edges


def build_graph(nodes, edges):
    """构建Graph"""
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
    return g


def find_largest_cc(graph):
    """找最大连通分量"""
    all_nodes = graph.get_all_nodes()
    visited = set()
    largest_cc = set()

    for start in all_nodes:
        if start in visited:
            continue
        component = set()
        queue = deque([start])
        visited.add(start)
        while queue:
            node = queue.popleft()
            component.add(node)
            for n in graph.get_neighbors(node):
                if n['node'] not in visited:
                    visited.add(n['node'])
                    queue.append(n['node'])
        if len(component) > len(largest_cc):
            largest_cc = component

    return largest_cc


def count_cc(graph):
    """统计连通分量数量"""
    all_nodes = graph.get_all_nodes()
    visited = set()
    count = 0
    for node in all_nodes:
        if node not in visited:
            count += 1
            queue = deque([node])
            while queue:
                n = queue.popleft()
                if n in visited:
                    continue
                visited.add(n)
                for neighbor in graph.get_neighbors(n):
                    if neighbor['node'] not in visited:
                        queue.append(neighbor['node'])
    return count


def load_poi_location_nodes():
    """加载POI的location_node_id"""
    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    poi_nodes = {'attractions': {}, 'buildings': {}, 'facilities': {}, 'foods': {}}

    for poi_type in ['attractions', 'buildings', 'facilities', 'foods']:
        if poi_type == 'attractions':
            filename = 'attractions.json'
            key = 'attractions'
        elif poi_type == 'buildings':
            filename = 'buildings.json'
            key = 'buildings'
        elif poi_type == 'facilities':
            filename = 'facilities.json'
            key = 'facilities'
        else:
            filename = 'foods.json'
            key = 'foods'

        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get(key, []):
                    node_id = item.get('location_node_id')
                    if node_id:
                        poi_nodes[poi_type][item['id']] = node_id

    return poi_nodes


def main():
    print("=" * 60)
    print("道路网络验证")
    print("=" * 60)

    # 1. 加载道路网络
    print("\n[1] 加载道路网络...")
    nodes, edges = load_road_network()
    print(f"    道路节点数: {len(nodes)}")
    print(f"    道路边数: {len(edges)}")

    if not nodes:
        print("错误：没有找到道路节点数据！")
        return

    # 2. 构建图
    print("\n[2] 构建道路图...")
    graph = build_graph(nodes, edges)
    print(f"    图节点数: {graph.node_count()}")
    print(f"    图边数: {graph.edge_count()}")

    # 3. 检查连通分量
    print("\n[3] 检查连通分量...")
    cc_count = count_cc(graph)
    largest_cc = find_largest_cc(graph)
    print(f"    连通分量数量: {cc_count}")
    print(f"    最大连通分量大小: {len(largest_cc)}")

    # 4. 加载POI
    print("\n[4] 加载POI location_node_id...")
    poi_nodes = load_poi_location_nodes()
    for poi_type, mapping in poi_nodes.items():
        print(f"    {poi_type}: {len(mapping)} 个POI已挂载")

    # 5. 随机抽样测试Dijkstra
    print("\n[5] Dijkstra可达性测试...")
    largest_cc_list = list(largest_cc)
    if len(largest_cc_list) >= 2:
        print(f"    最大连通分量节点示例: {largest_cc_list[:5]}")

        # 随机测试10对节点
        success_count = 0
        for i in range(min(10, len(largest_cc_list) - 1)):
            src = largest_cc_list[i]
            dst = largest_cc_list[(i + 1) % len(largest_cc_list)]
            result = dijkstra(graph, src, dst, weight='distance')
            path = result.get('path', [])
            dist = result.get('distance', float('inf'))

            if path and dist < float('inf'):
                success_count += 1
                print(f"    {src[:20]}... -> {dst[:20]}...: dist={dist:.1f}m, path_len={len(path)}")
            else:
                print(f"    {src[:20]}... -> {dst[:20]}...: 不可达")

        print(f"    可达性测试: {success_count}/10 成功")

    # 6. 检查POI挂载
    print("\n[6] POI挂载检查...")
    all_valid = True
    for poi_type, mapping in poi_nodes.items():
        invalid = [poi_id for poi_id, node_id in mapping.items() if node_id not in largest_cc]
        if invalid:
            print(f"    {poi_type}: {len(invalid)} 个POI挂载到无效节点")
            all_valid = False
        else:
            print(f"    {poi_type}: 全部有效")

    if all_valid:
        print("\n    所有POI已挂载到最大连通分量节点")

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)


if __name__ == '__main__':
    main()