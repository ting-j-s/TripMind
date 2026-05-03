"""
室内导航测试

测试用例：
1. indoor_graphs.json 存在且至少2个建筑
2. 每个建筑有 entrance、elevator、room、edge
3. 大门到同层房间可达
4. 大门到高楼层房间可达
5. 高楼层房间路径必须经过电梯节点
6. 路径不是固定 stub
7. 不存在 building_id 时返回错误
8. 不存在 room 时返回错误
9. strategy=time 和 strategy=distance 均可运行
10. 返回结果包含 total_distance、total_time、algorithm
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.indoor_navigation_service import (
    load_indoor_graphs,
    get_building_data,
    build_indoor_graph,
    resolve_indoor_node,
    plan_indoor_route,
    list_buildings,
    get_building_info
)


class TestIndoorRoute:
    """室内导航测试类"""

    def test_indoor_graphs_exist(self):
        """测试 indoor_graphs.json 存在且至少2个建筑"""
        buildings = load_indoor_graphs()
        assert len(buildings) >= 2, f"需要至少2个建筑，当前只有{len(buildings)}个"
        print(f"  建筑数量: {len(buildings)}")
        for b in buildings:
            print(f"    {b['building_id']}: {b['building_name']}")

    def test_building_structure(self):
        """测试每个建筑有 entrance、elevator、room、edge"""
        buildings = load_indoor_graphs()

        for building in buildings:
            building_id = building.get('building_id')
            print(f"  检查 {building_id}:")

            # 检查 entrances
            entrances = building.get('entrances', [])
            assert len(entrances) > 0, f"{building_id} 缺少入口"
            print(f"    入口: {entrances}")

            # 检查 elevators
            elevators = building.get('elevators', [])
            assert len(elevators) > 0, f"{building_id} 缺少电梯"
            print(f"    电梯: {elevators}")

            # 检查 rooms
            nodes = building.get('nodes', [])
            rooms = [n for n in nodes if n.get('type') == 'room']
            assert len(rooms) > 0, f"{building_id} 缺少房间节点"
            print(f"    房间: {len(rooms)}个")

            # 检查 edges
            edges = building.get('edges', [])
            assert len(edges) > 0, f"{building_id} 缺少边"
            print(f"    边: {len(edges)}条")

    def test_same_floor_navigation(self):
        """测试大门到同层房间可达"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_101', strategy='time')
        assert result.get('success') == True, f"同层导航失败: {result.get('message')}"
        print(f"  gate -> room_101: 成功")
        print(f"    路径: {[n['name'] for n in result.get('path_nodes', [])]}")
        print(f"    距离: {result.get('total_distance')}m")
        print(f"    时间: {result.get('total_time')}s")

    def test_multi_floor_navigation(self):
        """测试大门到高楼层房间可达"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_301', strategy='time')
        assert result.get('success') == True, f"多层导航失败: {result.get('message')}"
        print(f"  gate -> room_301: 成功")
        print(f"    路径: {[n['name'] for n in result.get('path_nodes', [])]}")
        print(f"    距离: {result.get('total_distance')}m")
        print(f"    时间: {result.get('total_time')}s")

    def test_elevator_in_path(self):
        """测试高楼层房间路径必须经过电梯节点"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_301', strategy='time')
        assert result.get('success') == True

        path_nodes = result.get('path_nodes', [])
        elevator_nodes = [n for n in path_nodes if n.get('type') == 'elevator']

        assert len(elevator_nodes) >= 2, "多层路径必须经过电梯节点（至少2次：上电梯、下电梯）"
        print(f"  电梯节点: {[n['name'] for n in elevator_nodes]}")

    def test_path_not_stub(self):
        """测试路径不是固定假路径"""
        result1 = plan_indoor_route('BLD_001', 'gate', 'room_101', strategy='time')
        result2 = plan_indoor_route('BLD_001', 'gate', 'room_301', strategy='time')

        assert result1.get('success') == True
        assert result2.get('success') == True

        path1 = result1.get('path', [])
        path2 = result2.get('path', [])

        # 两条路径应该不同
        assert path1 != path2, "gate->room_101 和 gate->room_301 路径不应该相同"
        print(f"  gate -> room_101: {path1}")
        print(f"  gate -> room_301: {path2}")

    def test_invalid_building_id(self):
        """测试不存在 building_id 时返回错误"""
        result = plan_indoor_route('BLD_999', 'gate', 'room_101', strategy='time')
        assert result.get('success') == False, "应该返回错误"
        assert '不存在' in result.get('message', '') or '不存在' in str(result.get('message', '')), \
            f"错误信息应该包含 '不存在'，实际: {result.get('message')}"
        print(f"  错误信息: {result.get('message')}")

    def test_invalid_room(self):
        """测试不存在 room 时返回错误"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_999', strategy='time')
        assert result.get('success') == False, "应该返回错误"
        print(f"  错误信息: {result.get('message')}")

    def test_strategy_time(self):
        """测试 strategy=time 可以运行"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_301', strategy='time')
        assert result.get('success') == True
        assert result.get('total_time') > 0
        assert 'algorithm' in result
        print(f"  strategy=time: 时间={result.get('total_time')}s")

    def test_strategy_distance(self):
        """测试 strategy=distance 可以运行"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_301', strategy='distance')
        assert result.get('success') == True
        assert result.get('total_distance') > 0
        assert 'algorithm' in result
        print(f"  strategy=distance: 距离={result.get('total_distance')}m")

    def test_result_structure(self):
        """测试返回结果包含必要字段"""
        result = plan_indoor_route('BLD_001', 'gate', 'room_301', strategy='time')
        assert result.get('success') == True

        assert 'total_distance' in result, "缺少 total_distance"
        assert 'total_time' in result, "缺少 total_time"
        assert 'algorithm' in result, "缺少 algorithm"
        assert 'path_nodes' in result, "缺少 path_nodes"
        assert 'path' in result, "缺少 path"

        print(f"  total_distance: {result.get('total_distance')}")
        print(f"  total_time: {result.get('total_time')}")
        print(f"  algorithm: {result.get('algorithm')}")

    def test_elevator_target(self):
        """测试以电梯为目标"""
        result = plan_indoor_route('BLD_001', 'gate', 'elevator', strategy='time')
        assert result.get('success') == True
        path_nodes = result.get('path_nodes', [])
        last_node = path_nodes[-1] if path_nodes else {}
        assert last_node.get('type') == 'elevator', "终点应该是电梯"
        print(f"  gate -> elevator: 成功，终点类型={last_node.get('type')}")


def run_tests():
    """运行所有测试"""
    print("=" * 50)
    print("室内导航测试")
    print("=" * 50)

    tester = TestIndoorRoute()

    tests = [
        ("indoor_graphs.json 存在且2个建筑", tester.test_indoor_graphs_exist),
        ("建筑结构完整", tester.test_building_structure),
        ("同层导航", tester.test_same_floor_navigation),
        ("多层导航", tester.test_multi_floor_navigation),
        ("电梯节点在路径中", tester.test_elevator_in_path),
        ("路径不是固定假路径", tester.test_path_not_stub),
        ("无效building_id错误", tester.test_invalid_building_id),
        ("无效room错误", tester.test_invalid_room),
        ("strategy=time", tester.test_strategy_time),
        ("strategy=distance", tester.test_strategy_distance),
        ("返回结果结构", tester.test_result_structure),
        ("电梯为目标", tester.test_elevator_target),
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