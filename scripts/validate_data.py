"""
数据验证脚本

功能：
1. 验证POI数据完整性
2. 检查数据规模是否满足课程要求
3. 验证POI挂载状态
4. 检查数据质量
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data import get_loader


def check_data_scale():
    """检查数据规模"""
    print("\n[1] 数据规模检查")
    print("-" * 40)

    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    requirements = {
        'attractions': 200,
        'buildings': 20,
        'facilities': 50,
        'foods': 50,
        'diaries': 30,
        'users': 10
    }

    all_pass = True

    # 直接读取JSON文件获取准确数量
    for filename, req_count in [
        ('attractions.json', requirements['attractions']),
        ('buildings.json', requirements['buildings']),
        ('facilities.json', requirements['facilities']),
        ('foods.json', requirements['foods']),
        ('diaries.json', requirements['diaries']),
        ('users.json', requirements['users'])
    ]:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                key = filename.replace('.json', '')
                items = data.get(key, data.get(key + 's', []))
                actual = len(items)
        else:
            actual = 0

        status = "✓" if actual >= req_count else "✗"
        if actual < req_count:
            all_pass = False
        print(f"    {key}: {actual} (要求 >= {req_count}) {status}")

    return all_pass


def check_poi_mounting():
    """检查POI挂载状态"""
    print("\n[2] POI挂载检查")
    print("-" * 40)

    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    poi_files = {
        'attractions': 'attractions.json',
        'buildings': 'buildings.json',
        'facilities': 'facilities.json',
        'foods': 'foods.json'
    }

    all_mounted = True
    for poi_type, filename in poi_files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"    {poi_type}: 文件不存在")
            all_mounted = False
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        key = poi_type
        items = data.get(key, [])

        with_location = sum(1 for item in items if item.get('location_node_id'))
        total = len(items)

        if with_location == total:
            print(f"    {poi_type}: {total}/{total} 已挂载 ✓")
        else:
            print(f"    {poi_type}: {with_location}/{total} 已挂载 ✗")
            all_mounted = False

    return all_mounted


def check_facility_types():
    """检查设施类型分布"""
    print("\n[3] 设施类型分布检查")
    print("-" * 40)

    data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(data_dir, 'backend', 'data')

    filepath = os.path.join(data_dir, 'facilities.json')
    if not os.path.exists(filepath):
        print("    设施文件不存在")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    items = data.get('facilities', [])
    type_counts = {}
    for item in items:
        t = item.get('type', '未知')
        type_counts[t] = type_counts.get(t, 0) + 1

    print(f"    设施类型数量: {len(type_counts)}")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"      {t}: {count}")

    # 课程要求10种以上类型
    if len(type_counts) >= 10:
        print(f"    类型数量满足要求(>=10) ✓")
        return True
    else:
        print(f"    类型数量不足(需要>=10) ✗")
        return False


def check_data_quality():
    """检查数据质量"""
    print("\n[4] 数据质量检查")
    print("-" * 40)

    loader = get_loader()
    all_pass = True

    # 检查景点
    attractions = loader.get_all_attractions()
    invalid_attractions = [a for a in attractions if not a.name or not a.x or not a.y]
    if invalid_attractions:
        print(f"    attractions: {len(invalid_attractions)} 个无效(无名称或坐标)")
        all_pass = False
    else:
        print(f"    attractions: 全部有效 ✓")

    # 检查建筑
    buildings = loader.get_all_buildings()
    invalid_buildings = [b for b in buildings if not b.name]
    if invalid_buildings:
        print(f"    buildings: {len(invalid_buildings)} 个无效(无名称)")
        all_pass = False
    else:
        print(f"    buildings: 全部有效 ✓")

    # 检查设施
    facilities = loader.get_all_facilities()
    invalid_facilities = [f for f in facilities if not f.name or not f.type]
    if invalid_facilities:
        print(f"    facilities: {len(invalid_facilities)} 个无效(无名称或类型)")
        all_pass = False
    else:
        print(f"    facilities: 全部有效 ✓")

    # 检查美食
    foods = loader.get_all_foods()
    invalid_foods = [f for f in foods if not f.name]
    if invalid_foods:
        print(f"    foods: {len(invalid_foods)} 个无效(无名称)")
        all_pass = False
    else:
        print(f"    foods: 全部有效 ✓")

    return all_pass


def main():
    print("=" * 60)
    print("数据验证")
    print("=" * 60)

    scale_ok = check_data_scale()
    mounting_ok = check_poi_mounting()
    types_ok = check_facility_types()
    quality_ok = check_data_quality()

    print("\n" + "=" * 60)
    if all([scale_ok, mounting_ok, types_ok, quality_ok]):
        print("验证通过 ✓")
    else:
        print("验证未通过 ✗")
        if not scale_ok:
            print("  - 数据规模不足")
        if not mounting_ok:
            print("  - POI挂载不完整")
        if not types_ok:
            print("  - 设施类型不足")
        if not quality_ok:
            print("  - 数据质量问题")
    print("=" * 60)


if __name__ == '__main__':
    main()