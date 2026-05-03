# 需求追踪矩阵 (Requirement Traceability Matrix)

## 1. 课程要求概述

本项目为北京邮电大学数据结构课程设计，要求实现以下功能模块：

| 章节 | 要求 | 对应模块 |
|------|------|---------|
| 3.1 | 旅游景区介绍及推荐 | attractions.py (景点列表/搜索/推荐) |
| 3.2 | 最短路径规划（Dijkstra） | route.py (室外路径/室内导航) |
| 3.3 | 场所查询（附近设施） | nearby.py (基于道路网络的附近查询) |
| 3.4 | 旅游日记分享 | diary.py (CRUD/搜索/评分/压缩) |
| 3.5 | 美食推荐 | food.py (列表/搜索/推荐) |
| 3.6 | 地图显示 | frontend/pages/map.html (Leaflet地图) |

## 2. 功能模块与API对应

### 2.1 旅游景区介绍及推荐 (3.1)

| 功能 | API端点 | 实现文件 | 状态 |
|------|---------|---------|------|
| 景点列表 | GET /api/attractions | attractions.py:18-62 | ✓ |
| 景点详情 | GET /api/attractions/<id> | attractions.py:65-82 | ✓ |
| 景点搜索 | GET /api/attractions/search | attractions.py:85-121 | ✓ |
| 景点推荐 | GET /api/attractions/recommend | attractions.py:124-173 | ✓ |
| 校园列表 | GET /api/attractions/campuses | attractions.py:176-189 | ✓ |
| 分类过滤 | ?campus_id= | attractions.py:37-39 | ✓ |
| 排序 | ?sort=heat/rating | attractions.py:42-47 | ✓ |
| Top-K排序 | top_k()函数 | sort.py:130-194 | ✓ |
| 模糊搜索 | fuzzy_search() | fuzzy_search.py | ✓ |

**数据模型**: backend/models/attraction.py

**核心算法**:
- Top-K排序: O(n log k)
- 模糊搜索: 编辑距离

### 2.2 最短路径规划 (3.2)

| 功能 | API端点 | 实现文件 | 状态 |
|------|---------|---------|------|
| 路径规划 | POST /api/route/plan | route.py | ✓ |
| 最短路径 | Dijkstra | dijkstra.py | ✓ |
| TSP多景点 | /api/route/tsp | route.py:tsp_route() | ✓ |
| 室内导航 | POST /api/route/indoor | route.py:indoor_route() | ✓ |
| 电梯跨层 | elevator边 | indoor_navigation_service.py | ✓ |

**核心算法**:
- Dijkstra: O((V+E) log V)
- TSP: 贪心 + 2-opt

### 2.3 场所查询 (3.3)

| 功能 | API端点 | 实现文件 | 状态 |
|------|---------|---------|------|
| 附近查询 | GET /api/nearby | nearby.py | ✓ |
| 道路距离 | Dijkstra | dijkstra.py | ✓ |
| 设施类型 | type字段 | facilities.json | ✓ |
| 排序 | ?sort=distance/rating | nearby.py:95-97 | ✓ |

**数据模型**: backend/models/facility.py

### 2.4 旅游日记分享 (3.4)

| 功能 | API端点 | 实现文件 | 状态 |
|------|---------|---------|------|
| 日记列表 | GET /api/diaries | diary.py:37-82 | ✓ |
| 日记详情 | GET /api/diary/<id> | diary.py:199-216 | ✓ |
| 创建日记 | POST /api/diary | diary.py:131-196 | ✓ |
| 更新日记 | PUT /api/diary/<id> | diary.py:219-259 | ✓ |
| 删除日记 | DELETE /api/diary/<id> | diary.py:262-282 | ✓ |
| 评分日记 | POST /api/diary/<id>/rate | diary.py:285-317 | ✓ |
| 全文搜索 | GET /api/diaries/search | diary.py:85-128 | ✓ |
| 按目的地 | GET /api/diaries/by-destination | 缺失 | ✗ |
| 标题精确搜索 | GET /api/diaries/title | 缺失 | ✗ |
| 压缩存储 | POST /api/diary/<id>/compress | 缺失 | ✗ |
| 解压读取 | POST /api/diary/<id>/decompress | 缺失 | ✗ |
| AIGC动画 | POST /api/aigc/animation | aigc.py | ✓ |

**数据模型**: backend/models/diary.py

**核心算法**:
- 霍夫曼压缩: compression.py:HuffmanCoding
- 全文搜索: TextSearchIndex (倒排索引)

### 2.5 美食推荐 (3.5)

| 功能 | API端点 | 实现文件 | 状态 |
|------|---------|---------|------|
| 美食列表 | GET /api/foods | food.py:136-219 | ✓ |
| 美食搜索 | GET /api/foods/search | food.py:222-276 | ✓ |
| 美食推荐 | GET /api/foods/recommend | food.py:279-330 | ✓ |
| 菜系列表 | GET /api/cuisines | food.py:333-343 | ✓ |
| 道路距离 | Dijkstra | dijkstra.py | ✓ |

**数据模型**: backend/models/food.py

### 2.6 地图显示 (3.6)

| 功能 | 文件 | 状态 |
|------|-----|------|
| 地图页面 | frontend/pages/map.html | ✓ |
| Leaflet集成 | map.html | ✓ |
| POI标记 | map.html | ✓ |
| 路径显示 | map.html | ✓ |
| 室内导航显示 | indoor_navigation_service.py | ✓ |

## 3. 核心数据结构实现检查

| 数据结构 | 要求 | 实现 | 状态 |
|---------|------|------|------|
| 图（邻接表） | 自己实现 | backend/core/graph.py | ✓ |
| 堆（优先队列） | 自己实现 | backend/core/heap.py | ✓ |
| 哈希表 | 自己实现 | backend/core/hashtable.py | ✓ |
| 链表 | 自己实现 | backend/core/linkedlist.py | ✓ |
| 排序算法 | 自己实现 | backend/core/sort.py | ✓ |

## 4. 缺失功能清单

### 4.1 日记模块缺失

1. **POST /api/diaries/by-destination** - 按景点筛选日记
   - 期望: GET /api/diaries/by-destination?location_id=xxx
   - 当前: diaries API 有 location_id 参数可用

2. **GET /api/diaries/title** - 标题精确搜索
   - 需要: HashTable按title索引

3. **POST /api/diary/<id>/compress** - 压缩存储
   - 需要: 调用HuffmanCoding.compress()

4. **POST /api/diary/<id>/decompress** - 解压读取
   - 需要: 调用HuffmanCoding.decompress()

### 4.2 景点模块缺失

1. **分类过滤** - categories字段
   - 当前仅有campus_id过滤

## 5. 代码质量检查

### 5.1 Top-K Anti-Pattern

以下文件存在 `top_k(data, len(data))` 问题，这会导致全量排序而非Top-K优化：

| 文件 | 行号 | 问题 |
|------|------|------|
| diary.py | 62, 67 | top_k(diaries, len(diaries), ...) |
| attractions.py | 43, 46, 156, 157, 161, 164 | top_k(attractions, len(attractions), ...) |
| food.py | 203, 205, 254, 314, 315, 319, 321 | top_k(foods, len(foods), ...) |

**问题**: 当传入k >= n时，top_k会退化为heap_sort，没有发挥Top-K的优化效果。
**修复**: 应使用实际的limit参数，如 `top_k(diaries, limit, ...)`

## 6. 测试覆盖

| 模块 | 测试文件 | 覆盖 |
|------|---------|------|
| 道路网络 | test_road_network.py | Dijkstra, 连通分量, POI挂载 |
| 附近查询 | test_nearby.py | 设施查询, 距离排序 |
| 美食 | test_food.py | 列表, 搜索, 推荐 |
| 数据规模 | test_data_scale.py | POI数量, 挂载率 |
| 室内导航 | test_indoor_route.py | 多层路径, 电梯 |

---

**最后更新**: 2026-05-03
**状态**: 部分功能缺失，需要修复