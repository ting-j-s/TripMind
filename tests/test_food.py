"""
food.py 路由测试

测试用例：
1. 测试美食列表获取
2. 测试按菜系过滤
3. 测试按距离排序
4. 测试搜索功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routes.food import (
    get_road_graph,
    find_nearest_road_node,
    calculate_road_distance,
    calc_straight_distance
)
from backend.data import get_loader
from backend.core import top_k


class TestFood:
    """food路由测试类"""

    def setup_method(self):
        """测试前准备"""
        from backend.data import get_loader
        self.loader = get_loader()

    def test_food_data_loading(self):
        """测试美食数据加载"""
        foods = self.loader.get_all_foods()
        assert len(foods) > 0
        print(f"  加载美食: {len(foods)} 个")

    def test_food_has_location_node(self):
        """测试美食是否包含location_node_id"""
        foods = self.loader.get_all_foods()

        with_location = 0
        for f in foods:
            if getattr(f, 'location_node_id', None):
                with_location += 1

        print(f"  有location_node_id: {with_location}/{len(foods)}")
        assert with_location > 0

    def test_food_distance_sorting(self):
        """测试美食距离排序"""
        foods = self.loader.get_all_foods()

        if not foods:
            print("  无美食数据，跳过")
            return

        graph = get_road_graph()
        nodes = list(graph.get_all_nodes())

        if not nodes:
            print("  道路网络为空，跳过")
            return

        # 使用第一个节点作为参考点
        src_node = nodes[0]

        # 计算每个美食的距离
        for f in foods:
            food_node = getattr(f, 'location_node_id', None)
            if food_node:
                f.distance = calculate_road_distance(graph, src_node, food_node)
            else:
                f.distance = float('inf')

        # 按距离排序
        sorted_foods = sorted(foods, key=lambda x: x.distance if x.distance else float('inf'))

        print(f"  排序后第一个: {sorted_foods[0].name}, 距离={sorted_foods[0].distance:.1f}m")

        # 验证排序正确
        for i in range(len(sorted_foods) - 1):
            d1 = sorted_foods[i].distance
            d2 = sorted_foods[i+1].distance
            if d1 != float('inf') and d2 != float('inf'):
                assert d1 <= d2, f"排序错误: {d1} > {d2}"

    def test_cuisine_filtering(self):
        """测试菜系过滤"""
        foods = self.loader.get_all_foods()

        cuisines = set()
        for f in foods:
            if f.cuisine:
                cuisines.add(f.cuisine)

        print(f"  菜系种类: {len(cuisines)}")
        for cuisine in list(cuisines)[:5]:
            count = len([f for f in foods if f.cuisine == cuisine])
            print(f"    {cuisine}: {count}")

    def test_road_distance_calculation(self):
        """测试道路距离计算"""
        graph = get_road_graph()
        foods = self.loader.get_all_foods()

        foods_with_node = [f for f in foods if getattr(f, 'location_node_id', None)]

        if foods_with_node and graph.node_count() > 0:
            src_node = list(graph.get_all_nodes())[0]
            food = foods_with_node[0]
            dst_node = food.location_node_id

            dist = calculate_road_distance(graph, src_node, dst_node)

            print(f"  {src_node[:20]}... -> {food.name}: {dist:.1f}m")
            assert dist >= 0


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("food.py 测试")
    print("=" * 50)

    tester = TestFood()
    tester.setup_method()  # 初始化测试数据

    tests = [
        ("美食数据加载", tester.test_food_data_loading),
        ("美食location_node_id", tester.test_food_has_location_node),
        ("美食距离排序", tester.test_food_distance_sorting),
        ("菜系过滤", tester.test_cuisine_filtering),
        ("道路距离计算", tester.test_road_distance_calculation),
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