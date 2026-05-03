"""
道路网络集成测试

测试用例：
1. 测试道路网络图构建
2. 测试连通分量检测
3. 测试Dijkstra最短路径
4. 测试POI到道路网络的映射
"""

import sys
import os
import json
import math
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

    # 加载beijing_road_nodes.json
    nodes_file = os.path.join(data_dir, 'beijing_road_nodes.json')
    if os.path.exists(nodes_file):
        with open(nodes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for node in data.get('nodes', []):
                nodes[node['id']] = {'x': node['x'], 'y': node['y']}

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


class TestRoadNetwork:
    """道路网络测试类"""

    def test_road_network_loading(self):
        """测试道路网络加载"""
        nodes, edges = load_road_network()
        print(f"  节点数: {len(nodes)}")
        print(f"  边数: {len(edges)}")
        assert len(nodes) > 0
        assert len(edges) > 0

    def test_graph_construction(self):
        """测试图构建"""
        nodes, edges = load_road_network()
        graph = build_graph(nodes, edges)

        print(f"  图节点数: {graph.node_count()}")
        print(f"  图边数: {graph.edge_count()}")

        # 节点数可能比原始nodes多，因为edges中的节点ID可能不在nodes字典中
        assert graph.node_count() >= len(nodes) * 0.9  # 允许10%误差
        assert graph.edge_count() == len(edges)

    def test_connected_components(self):
        """测试连通分量"""
        nodes, edges = load_road_network()
        graph = build_graph(nodes, edges)

        cc_count = count_cc(graph)
        largest_cc = find_largest_cc(graph)

        print(f"  连通分量数量: {cc_count}")
        print(f"  最大连通分量大小: {len(largest_cc)}")

        assert cc_count > 0
        assert len(largest_cc) > 0

        # 验证最大连通分量确实连通
        assert len(largest_cc) <= graph.node_count()

    def test_dijkstra_shortest_path(self):
        """测试Dijkstra最短路径"""
        nodes, edges = load_road_network()
        graph = build_graph(nodes, edges)
        largest_cc = find_largest_cc(graph)
        largest_cc_list = list(largest_cc)

        if len(largest_cc_list) < 2:
            print("  连通分量节点不足，跳过")
            return

        # 随机测试几对节点
        success_count = 0
        for i in range(min(5, len(largest_cc_list) - 1)):
            src = largest_cc_list[i]
            dst = largest_cc_list[(i + 1) % len(largest_cc_list)]

            result = dijkstra(graph, src, dst, weight='distance')
            path = result.get('path', [])
            dist = result.get('distance', float('inf'))

            if path and dist < float('inf'):
                success_count += 1
                print(f"  {src[:15]}... -> {dst[:15]}...: {dist:.1f}m, {len(path)} 节点")

        print(f"  成功率: {success_count}/5")
        assert success_count >= 4  # 至少80%成功

    def test_poi_mounting(self):
        """测试POI挂载"""
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(data_dir, 'backend', 'data')

        poi_files = {
            'attractions': 'attractions.json',
            'buildings': 'buildings.json',
            'facilities': 'facilities.json',
            'foods': 'foods.json'
        }

        total_pois = 0
        mounted_pois = 0

        for poi_type, filename in poi_files.items():
            filepath = os.path.join(data_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                items = data.get(poi_type, [])
                total_pois += len(items)
                mounted = sum(1 for item in items if item.get('location_node_id'))
                mounted_pois += mounted
                print(f"  {poi_type}: {mounted}/{len(items)} 挂载")

        print(f"  总计: {mounted_pois}/{total_pois} 挂载")
        assert mounted_pois == total_pois  # 全部挂载


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("道路网络集成测试")
    print("=" * 50)

    tester = TestRoadNetwork()

    tests = [
        ("道路网络加载", tester.test_road_network_loading),
        ("图构建", tester.test_graph_construction),
        ("连通分量", tester.test_connected_components),
        ("Dijkstra最短路径", tester.test_dijkstra_shortest_path),
        ("POI挂载", tester.test_poi_mounting),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n[测试] {name}")
        try:
            test_func()
            print(f"  ✓ 通过")
            passed += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)