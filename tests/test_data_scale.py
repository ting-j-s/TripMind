"""
数据规模测试

课程要求：
- 景点（attractions）: 200+
- 建筑（buildings）: 20+
- 设施（facilities）: 50+, 类型10+
- 美食（foods）: 50+
- 日记（diaries）: 30+
- 用户（users）: 10+
- 道路边（roads）: 200+
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data import get_loader


class TestDataScale:
    """数据规模测试类"""

    def test_attractions_scale(self):
        """测试景点规模"""
        loader = get_loader()

        # 直接读取JSON文件获取准确数量
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(data_dir, 'backend', 'data')

        filepath = os.path.join(data_dir, 'attractions.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        attractions = data.get('attractions', [])
        print(f"  attractions: {len(attractions)} (要求 >= 200)")

        # 使用loader的过滤后数量
        filtered_attractions = loader.get_all_attractions()
        print(f"  (loader过滤后: {len(filtered_attractions)})")

        assert len(attractions) >= 200, f"景点数量不足: {len(attractions)} < 200"

    def test_buildings_scale(self):
        """测试建筑规模"""
        loader = get_loader()
        buildings = loader.get_all_buildings()

        print(f"  buildings: {len(buildings)} (要求 >= 20)")
        assert len(buildings) >= 20, f"建筑数量不足: {len(buildings)} < 20"

    def test_facilities_scale(self):
        """测试设施规模"""
        loader = get_loader()
        facilities = loader.get_all_facilities()

        print(f"  facilities: {len(facilities)} (要求 >= 50)")
        assert len(facilities) >= 50, f"设施数量不足: {len(facilities)} < 50"

    def test_facilities_types(self):
        """测试设施类型数量"""
        loader = get_loader()
        facilities = loader.get_all_facilities()

        types = set()
        for f in facilities:
            if f.type:
                types.add(f.type)

        print(f"  设施类型: {len(types)} (要求 >= 10)")
        print(f"  类型列表: {sorted(types)}")

        assert len(types) >= 10, f"设施类型不足: {len(types)} < 10"

    def test_foods_scale(self):
        """测试美食规模"""
        loader = get_loader()
        foods = loader.get_all_foods()

        print(f"  foods: {len(foods)} (要求 >= 50)")
        assert len(foods) >= 50, f"美食数量不足: {len(foods)} < 50"

    def test_diaries_scale(self):
        """测试日记规模"""
        loader = get_loader()
        diaries = loader.get_all_diaries()

        print(f"  diaries: {len(diaries)} (要求 >= 30)")
        assert len(diaries) >= 30, f"日记数量不足: {len(diaries)} < 30"

    def test_users_scale(self):
        """测试用户规模"""
        loader = get_loader()
        users = loader.get_all_users() if hasattr(loader, 'get_all_users') else []

        # 尝试直接读取
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(data_dir, 'backend', 'data')

        filepath = os.path.join(data_dir, 'users.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        users = data.get('users', [])
        print(f"  users: {len(users)} (要求 >= 10)")
        assert len(users) >= 10, f"用户数量不足: {len(users)} < 10"

    def test_roads_scale(self):
        """测试道路边规模"""
        loader = get_loader()
        roads = loader.get_all_roads()

        print(f"  roads: {len(roads)} (要求 >= 200)")
        assert len(roads) >= 200, f"道路边数量不足: {len(roads)} < 200"

    def test_road_network_scale(self):
        """测试道路网络规模"""
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(data_dir, 'backend', 'data')

        # 读取roads.json
        filepath = os.path.join(data_dir, 'roads.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        roads = data.get('roads', [])
        print(f"  道路边(roads.json): {len(roads)}")

        # 读取节点
        nodes_file = os.path.join(data_dir, 'beijing_road_nodes.json')
        with open(nodes_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        nodes = data.get('nodes', [])
        print(f"  道路节点: {len(nodes)}")

        assert len(roads) >= 200, f"道路边不足"
        assert len(nodes) >= 200, f"道路节点不足"


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("数据规模测试")
    print("=" * 50)

    tester = TestDataScale()

    tests = [
        ("景点规模", tester.test_attractions_scale),
        ("建筑规模", tester.test_buildings_scale),
        ("设施规模", tester.test_facilities_scale),
        ("设施类型", tester.test_facilities_types),
        ("美食规模", tester.test_foods_scale),
        ("日记规模", tester.test_diaries_scale),
        ("用户规模", tester.test_users_scale),
        ("道路边规模", tester.test_roads_scale),
        ("道路网络规模", tester.test_road_network_scale),
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