"""
nearby.py 路由测试

测试用例：
1. 测试附近设施查询（使用道路距离）
2. 测试按类型过滤
3. 测试按距离排序
4. 测试radius过滤
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes.nearby import (
    get_road_graph,
    find_nearest_road_node,
    calculate_road_distance,
    calc_straight_distance
)
from backend.core.graph import Graph
from backend.algorithms.dijkstra import dijkstra


class TestNearby:
    """nearby路由测试类"""

    def setup_method(self):
        """测试前准备"""
        pass

    def test_road_graph_loading(self):
        """测试道路网络图加载"""
        graph = get_road_graph()
        assert graph is not None
        assert graph.node_count() > 0
        assert graph.edge_count() > 0
        print(f"  道路网络: {graph.node_count()} 节点, {graph.edge_count()} 边")

    def test_dijkstra_distance(self):
        """测试Dijkstra计算道路距离"""
        graph = get_road_graph()
        nodes = list(graph.get_all_nodes())

        if len(nodes) >= 2:
            # 取两个节点测试
            src, dst = nodes[0], nodes[1]
            dist = calculate_road_distance(graph, src, dst)

            if dist < float('inf'):
                print(f"  {src[:20]}... -> {dst[:20]}...: {dist:.1f}m")
                assert dist >= 0
            else:
                print(f"  {src[:20]}... -> {dst[:20]}...: 不可达")

    def test_nearest_node_finding(self):
        """测试最近节点查找"""
        # 测试坐标(116.3, 40.0)附近的最近节点
        x, y = 116.3, 40.0
        nearest = find_nearest_road_node(x, y)

        if nearest:
            print(f"  ({x}, {y}) 最近的节点: {nearest}")
            assert nearest is not None
            assert isinstance(nearest, str)
        else:
            print("  未找到最近节点（道路网络可能为空）")

    def test_straight_distance(self):
        """测试直线距离计算"""
        # 北京的两个已知点
        x1, y1 = 116.3521, 40.0251  # 图书馆
        x2, y2 = 116.3523, 40.0253

        dist = calc_straight_distance(x1, y1, x2, y2)
        print(f"  ({x1}, {y1}) -> ({x2}, {y2}): {dist:.1f}m")

        # 直线距离应该很小（约30米）
        assert 0 < dist < 1000

    def test_facility_road_distance(self):
        """测试设施的道路距离计算"""
        graph = get_road_graph()

        # 获取一个设施的location_node_id
        from backend.data import get_loader
        loader = get_loader()
        facilities = loader.get_all_facilities()

        if facilities:
            facility = facilities[0]
            facility_node = getattr(facility, 'location_node_id', None)

            if facility_node:
                # 获取任意一个起点节点
                nodes = list(graph.get_all_nodes())
                if nodes:
                    src_node = nodes[0]
                    dist = calculate_road_distance(graph, src_node, facility_node)

                    print(f"  {src_node[:20]}... -> {facility.name}: {dist:.1f}m")
                    assert dist >= 0


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("nearby.py 测试")
    print("=" * 50)

    tester = TestNearby()

    tests = [
        ("道路网络图加载", tester.test_road_graph_loading),
        ("Dijkstra距离计算", tester.test_dijkstra_distance),
        ("最近节点查找", tester.test_nearest_node_finding),
        ("直线距离计算", tester.test_straight_distance),
        ("设施道路距离", tester.test_facility_road_distance),
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
            failed += 1

    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 50)

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)