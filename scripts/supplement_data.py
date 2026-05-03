"""
数据规模补齐脚本

生成足够的POI数据以满足课程要求：
- attractions >= 200
- buildings >= 20
- facilities >= 50, 类别 >= 10
- foods >= 50
- diaries >= 30
- users >= 10
"""

import os
import sys
import json
import random
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.graph import Graph
from backend.algorithms.dijkstra import dijkstra

# 数据目录
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend', 'data')


def load_existing_data():
    """加载现有数据"""
    data = {}
    files = ['attractions.json', 'buildings.json', 'facilities.json', 'foods.json', 'diaries.json', 'users.json']
    for f in files:
        filepath = os.path.join(DATA_DIR, f)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as fp:
                key = f.replace('.json', '')
                # 特殊处理
                if f == 'attractions.json':
                    data['attractions'] = json.load(fp).get('attractions', [])
                elif f == 'buildings.json':
                    data['buildings'] = json.load(fp).get('buildings', [])
                elif f == 'facilities.json':
                    data['facilities'] = json.load(fp).get('facilities', [])
                elif f == 'foods.json':
                    data['foods'] = json.load(fp).get('foods', [])
                elif f == 'diaries.json':
                    data['diaries'] = json.load(fp).get('diaries', [])
                elif f == 'users.json':
                    data['users'] = json.load(fp).get('users', [])
        else:
            data[f.replace('.json', '')] = []
    return data


def load_road_network():
    """加载道路网络"""
    nodes = {}
    edges = []

    # 加载roads.json
    roads_file = os.path.join(DATA_DIR, 'roads.json')
    if os.path.exists(roads_file):
        with open(roads_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for road in data.get('roads', []):
                edges.append({
                    'from': road['from'],
                    'to': road['to'],
                    'distance': road['distance']
                })

    # 加载节点
    nodes_file = os.path.join(DATA_DIR, 'beijing_road_nodes.json')
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
        g.add_edge(edge['from'], edge['to'], distance=edge['distance'],
                   time=edge['distance'] / 30 * 3.6, ideal_speed=30, congestion=1.0, road_types=['步行', '自行车', '驾车'])
    return g


def find_largest_cc(graph):
    """找最大连通分量"""
    from collections import deque
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


def calc_distance(x1, y1, x2, y2):
    """计算两点间直线距离（米）"""
    R = 6371000
    lat1, lon1 = math.radians(y1), math.radians(x1)
    lat2, lon2 = math.radians(y2), math.radians(x2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def find_nearest_node(x, y, nodes, valid_nodes):
    """找最近节点"""
    nearest, min_dist = None, float('inf')
    for node_id in valid_nodes:
        if node_id not in nodes:
            continue
        d = calc_distance(x, y, nodes[node_id]['x'], nodes[node_id]['y'])
        if d < min_dist:
            min_dist, nearest = d, node_id
    return nearest


def stable_hash_node(poi_id, valid_nodes):
    """哈希分配节点"""
    if not valid_nodes:
        return None
    idx = sum(ord(c) for c in str(poi_id)) % len(valid_nodes)
    return list(valid_nodes)[idx]


def generate_more_attractions(existing, target, nodes, valid_nodes):
    """生成更多景点"""
    names = [
        "故宫", "天坛", "颐和园", "圆明园", "长城", "北海", "景山", "香山",
        "欢乐谷", "动物园", "植物园", "中山公园", "陶然亭", "玉渊潭", "朝阳公园",
        "鸟巢", "水立方", "国家大剧院", "国家博物馆", "科技馆", "自然博物馆",
        "南锣鼓巷", "什刹海", "798艺术区", "三里屯", "前门", "王府井", "世界公园",
        "野生动物园", "十三陵", "雍和宫", "大觉寺", "红螺寺", "潭柘寺",
        "胡同", "四合院", "老北京茶馆", "瑞蚨祥", "内联升", "同仁堂", "步瀛斋",
        "国贸", "CBD", "金融街", "中关村", "望京", "亦庄", "顺义", "怀柔",
        "密云", "平谷", "延庆", "房山", "门头沟", "石景山", "丰台",
        "天安门", "人民大会堂", "人民英雄纪念碑", "中山纪念堂",
        "八达岭", "慕田峪", "司马台", "金山岭", "居庸关", "喜峰口",
        "周口店", "琉璃河", "云居寺", "白草畔", "百花山", "灵山",
        "北海公园", "中南海", "劳动人民文化宫", "地坛", "日坛", "月坛",
        "恭王府", "醇亲王府", "礼王府", "郑王府", "庄王府", "端郡王府",
        "银锭桥", "鼓楼", "钟楼", "永定门", "正阳门", "崇文门", "宣武门",
        "西单", "东单", "西四", "东四", "菜市口", "虎坊桥", "磁器口"
    ]

    campuses = ["CAMPUS001", "CAMPUS002", "CAMPUS003", "CAMPUS004", "CAMPUS005"]

    # 北京典型坐标范围
    base_lon, base_lat = 116.3, 39.9
    lon_range, lat_range = 0.4, 0.35

    while len(existing) < target:
        idx = len(existing) + 1
        lon = base_lon + random.random() * lon_range
        lat = base_lat + random.random() * lat_range
        nearest = find_nearest_node(lon, lat, nodes, valid_nodes)
        if not nearest:
            nearest = stable_hash_node(f"ATTR_BJ_EX{idx}", valid_nodes)

        heat = random.randint(1000, 90000)
        rating = round(random.uniform(3.5, 5.0), 1)

        new_attr = {
            "id": f"ATTR_BJ_EX{idx:04d}",
            "name": random.choice(names) + ["", "遗址", "公园", "广场", "博物馆", "文化中心"][random.randint(0, 5)],
            "type": "景点",
            "campus_id": None,
            "x": round(lon, 6),
            "y": round(lat, 6),
            "heat": heat,
            "rating": rating,
            "tags": random.sample(["历史", "博物馆", "古建筑", "公园", "园林", "湖泊", "运动", "娱乐", "亲子", "自然", "宗教", "文化", "购物", "美食", "摄影"], k=3),
            "description": "北京著名景点",
            "image_url": None,
            "location_node_id": nearest
        }
        existing.append(new_attr)


def generate_more_buildings(existing, target, nodes, valid_nodes):
    """生成更多建筑"""
    types = ["教学楼", "食堂", "宿舍楼", "体育馆", "图书馆", "实验楼", "行政楼", "活动中心", "游泳馆", "体育场", "篮球场", "网球场", "超市", "医院", "银行"]
    campuses = ["CAMPUS001", "CAMPUS002", "CAMPUS003", "CAMPUS004", "CAMPUS005"]

    campus_coords = {
        "CAMPUS001": (116.352, 40.025),
        "CAMPUS002": (116.324, 40.0),
        "CAMPUS003": (116.307, 39.989),
        "CAMPUS004": (116.365, 39.961),
        "CAMPUS005": (116.353, 39.943)
    }

    while len(existing) < target:
        idx = len(existing) + 1
        campus = random.choice(campuses)
        base_lon, base_lat = campus_coords[campus]
        lon = base_lon + random.uniform(-0.02, 0.02)
        lat = base_lat + random.uniform(-0.02, 0.02)
        nearest = find_nearest_node(lon, lat, nodes, valid_nodes) or stable_hash_node(f"BLD_{idx}", valid_nodes)

        new_bld = {
            "id": f"BLD_{idx:04d}",
            "name": f"建筑{idx}",
            "type": random.choice(types),
            "campus_id": campus,
            "x": round(lon, 6),
            "y": round(lat, 6),
            "floors": random.randint(1, 10),
            "rooms": [f"{random.randint(1,9)}0{random.randint(1,9)}" for _ in range(random.randint(3, 8))],
            "elevators": ["A", "B"] if random.random() > 0.5 else [],
            "entrances": ["东门", "西门"] if random.random() > 0.3 else ["正门"],
            "location_node_id": nearest
        }
        existing.append(new_bld)


def generate_more_facilities(existing, target, nodes, valid_nodes):
    """生成更多设施"""
    facility_types = [
        "超市", "洗手间", "咖啡馆", "ATM", "打印店", "书店", "药店",
        "水果店", "快递站", "自行车棚", "停车场", "自动售货机", "淋浴间",
        "医务室", "心理咨询室", "就业指导中心", "体育馆器材室", "学生活动中心"
    ]

    campuses = ["CAMPUS001", "CAMPUS002", "CAMPUS003", "CAMPUS004", "CAMPUS005"]
    campus_coords = {
        "CAMPUS001": (116.352, 40.025), "CAMPUS002": (116.324, 40.0),
        "CAMPUS003": (116.307, 39.989), "CAMPUS004": (116.365, 39.961), "CAMPUS005": (116.353, 39.943)
    }

    while len(existing) < target:
        idx = len(existing) + 1
        campus = random.choice(campuses)
        base_lon, base_lat = campus_coords[campus]
        lon = base_lon + random.uniform(-0.02, 0.02)
        lat = base_lat + random.uniform(-0.02, 0.02)
        nearest = find_nearest_node(lon, lat, nodes, valid_nodes) or stable_hash_node(f"FAC_EX{idx}", valid_nodes)

        new_fac = {
            "id": f"FAC_EX{idx:04d}",
            "name": f"设施{idx}",
            "type": random.choice(facility_types),
            "campus_id": campus,
            "x": round(lon, 6),
            "y": round(lat, 6),
            "location_node_id": nearest
        }
        existing.append(new_fac)


def generate_more_foods(existing, target, nodes, valid_nodes):
    """生成更多美食"""
    cuisines = ["川菜", "湘菜", "粤菜", "鲁菜", "浙菜", "闽菜", "苏菜", "徽菜", "东北菜", "清真菜", "西餐", "日料", "韩餐", "东南亚菜", "快餐", "小吃", "火锅", "烧烤", "串串", "麻辣烫", "黄焖鸡", "沙县小吃", "兰州拉面", "刀削面", "炸酱面", "卤肉饭", "盖浇饭", "石锅拌饭", "咖喱饭", "寿司", "拉面", "饺子", "包子", "煎饼", "肉夹馍", "凉皮", "肉骨茶", "煲仔饭", "肠粉", "叉烧饭", "蛋炒饭", "炒面", "炒河粉", "酸辣粉", "过桥米线", "瓦罐汤", "卤味", "酱牛肉", "烤鸭", "炸鸡", "汉堡", "披萨", "三明治", "沙拉", "冰淇淋", "奶茶", "果汁", "咖啡", "甜品", "蛋糕", "面包", "饼干", "坚果", "果脯", "牛肉干", "鱼豆腐", "魔芋丝", "鸡爪", "鸭脖", "周黑鸭", "绝味", "煌上煌", "久久鸭", "紫燕", "廖记", "留夫鸭", "煌上煌", "周黑鸭"]

    restaurants = ["食堂一层", "食堂二层", "食堂三层", "商业街A座", "商业街B座", "小吃城", "美食广场", "教工食堂", "清真食堂", "西餐厅", "咖啡厅", "便利店", "面包房", "水果店", "奶茶店", "快餐店"]

    campuses = ["CAMPUS001", "CAMPUS002", "CAMPUS003", "CAMPUS004", "CAMPUS005"]
    campus_coords = {
        "CAMPUS001": (116.352, 40.025), "CAMPUS002": (116.324, 40.0),
        "CAMPUS003": (116.307, 39.989), "CAMPUS004": (116.365, 39.961), "CAMPUS005": (116.353, 39.943)
    }

    while len(existing) < target:
        idx = len(existing) + 1
        campus = random.choice(campuses)
        base_lon, base_lat = campus_coords[campus]
        lon = base_lon + random.uniform(-0.02, 0.02)
        lat = base_lat + random.uniform(-0.02, 0.02)
        nearest = find_nearest_node(lon, lat, nodes, valid_nodes) or stable_hash_node(f"FOOD_EX{idx}", valid_nodes)

        new_food = {
            "id": f"FOOD_EX{idx:04d}",
            "name": random.choice(cuisines) + ["盖饭", "面条", "套餐", "炒菜", "小吃", "饭", "面", "粉"][random.randint(0, 7)],
            "cuisine": random.choice(cuisines),
            "restaurant": random.choice(restaurants),
            "campus_id": campus,
            "x": round(lon, 6),
            "y": round(lat, 6),
            "heat": random.randint(100, 900),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "price": round(random.uniform(8, 80), 1),
            "location_node_id": nearest
        }
        existing.append(new_food)


def generate_more_diaries(existing, target):
    """生成更多日记"""
    user_ids = ["user_001", "user_002", "user_003", "user_004", "user_005"]
    locations = ["ATTR_BJ_001", "ATTR_BJ_002", "ATTR_BJ_003", "ATTR_BJ_004", "ATTR_BJ_005",
                 "ATTR_CAMPUS001_001", "ATTR_CAMPUS001_002", "ATTR_CAMPUS002_001", "ATTR_CAMPUS003_001"]

    titles = [
        "难忘的旅行经历", "北京一日游", "校园漫步", "周末出游记",
        "发现北京之美", "美食探店", "文化之旅", "自然风光",
        "历史遗迹探访", "摄影之旅", "骑行日记", "徒步记录",
        "旅行随笔", "景点打卡", "深度游北京", "周末好去处",
        "探索北京", "旅行感悟", "城市漫游", "风景如画"
    ]

    contents = [
        "今天的旅行非常愉快！天气很好，阳光明媚。",
        "这座古老的建筑真宏伟，让人不禁感叹历史的沧桑。",
        "美食真的太好吃了，下次一定还要再来！",
        "风景如画，拍照留念。",
        "感受到了这座城市独特的魅力。",
        "人很多但是风景确实不错，值得一来。",
        "下次带上家人一起来玩。",
        "交通很方便，推荐大家来。",
        "这次旅行让我收获很多，了解了很多历史文化。",
        "环境优美，设施完善，是休闲的好去处。"
    ]

    while len(existing) < target:
        idx = len(existing) + 1
        new_diary = {
            "id": f"diary_{idx:04d}",
            "user_id": random.choice(user_ids),
            "title": random.choice(titles) + f" {idx}",
            "content": "\n".join(random.sample(contents, k=3)),
            "images": [],
            "videos": [],
            "location_id": random.choice(locations),
            "create_time": f"2026-0{random.randint(1,5)}-{random.randint(10,28):02d} {random.randint(8,20):02d}:{random.randint(0,59):02d}:00",
            "view_count": random.randint(10, 500),
            "ratings": [round(random.uniform(3.5, 5.0), 1) for _ in range(random.randint(1, 5))]
        }
        existing.append(new_diary)


def generate_more_users(existing, target):
    """生成更多用户"""
    while len(existing) < target:
        idx = len(existing) + 1
        new_user = {
            "id": f"user_{idx:03d}",
            "username": f"user{idx:03d}",
            "password_hash": "123456",  # 简化，实际应该加密
            "interests": random.sample(["历史", "博物馆", "美食", "摄影", "运动", "自然", "文化", "购物", "娱乐", "休闲"], k=3),
            "favorites": [],
            "visited": [],
            "create_time": f"2026-0{random.randint(1,4)}-{random.randint(10,28):02d} {random.randint(8,20):02d}:{random.randint(0,59):02d}:00"
        }
        existing.append(new_user)


def save_data(data):
    """保存数据"""
    for key, items in data.items():
        if key == 'attractions':
            with open(os.path.join(DATA_DIR, 'attractions.json'), 'w', encoding='utf-8') as f:
                json.dump({"attractions": items}, f, ensure_ascii=False, indent=2)
        elif key == 'buildings':
            with open(os.path.join(DATA_DIR, 'buildings.json'), 'w', encoding='utf-8') as f:
                json.dump({"buildings": items}, f, ensure_ascii=False, indent=2)
        elif key == 'facilities':
            with open(os.path.join(DATA_DIR, 'facilities.json'), 'w', encoding='utf-8') as f:
                json.dump({"facilities": items}, f, ensure_ascii=False, indent=2)
        elif key == 'foods':
            with open(os.path.join(DATA_DIR, 'foods.json'), 'w', encoding='utf-8') as f:
                json.dump({"foods": items}, f, ensure_ascii=False, indent=2)
        elif key == 'diaries':
            with open(os.path.join(DATA_DIR, 'diaries.json'), 'w', encoding='utf-8') as f:
                json.dump({"diaries": items}, f, ensure_ascii=False, indent=2)
        elif key == 'users':
            with open(os.path.join(DATA_DIR, 'users.json'), 'w', encoding='utf-8') as f:
                json.dump({"users": items}, f, ensure_ascii=False, indent=2)


def main():
    print("=" * 60)
    print("数据规模补齐")
    print("=" * 60)

    # 加载现有数据
    print("\n[1] 加载现有数据...")
    data = load_existing_data()
    print(f"    attractions: {len(data['attractions'])}")
    print(f"    buildings: {len(data['buildings'])}")
    print(f"    facilities: {len(data['facilities'])}")
    print(f"    foods: {len(data['foods'])}")
    print(f"    diaries: {len(data['diaries'])}")
    print(f"    users: {len(data['users'])}")

    # 加载道路网络
    print("\n[2] 加载道路网络...")
    nodes, edges = load_road_network()
    graph = build_graph(nodes, edges)
    largest_cc = find_largest_cc(graph)
    print(f"    道路节点: {len(nodes)}, 最大连通分量: {len(largest_cc)}")

    # 补齐数据
    print("\n[3] 补齐数据...")

    if len(data['attractions']) < 200:
        generate_more_attractions(data['attractions'], 200, nodes, largest_cc)
        print(f"    attractions: {len(data['attractions'])}")

    if len(data['buildings']) < 20:
        generate_more_buildings(data['buildings'], 20, nodes, largest_cc)
        print(f"    buildings: {len(data['buildings'])}")

    if len(data['facilities']) < 50:
        generate_more_facilities(data['facilities'], 50, nodes, largest_cc)
        print(f"    facilities: {len(data['facilities'])}")

    if len(data['foods']) < 50:
        generate_more_foods(data['foods'], 50, nodes, largest_cc)
        print(f"    foods: {len(data['foods'])}")

    if len(data['diaries']) < 30:
        generate_more_diaries(data['diaries'], 30)
        print(f"    diaries: {len(data['diaries'])}")

    if len(data['users']) < 10:
        generate_more_users(data['users'], 10)
        print(f"    users: {len(data['users'])}")

    # 保存
    print("\n[4] 保存数据...")
    save_data(data)

    # 检查设施类别
    facility_types = set(f['type'] for f in data['facilities'])
    print(f"    设施类别: {len(facility_types)} 种")
    if len(facility_types) < 10:
        print(f"    警告: 设施类别只有 {len(facility_types)} 种，需要 >= 10 种")

    print("\n" + "=" * 60)
    print("数据补齐完成")
    print("=" * 60)


if __name__ == '__main__':
    main()