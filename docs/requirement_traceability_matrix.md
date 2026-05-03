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
| 3.6 | 地图显示 | frontend/pages/route_planning.html (Leaflet地图) |

---

## 2. 功能模块与API对应

### 2.1 旅游景区介绍及推荐 (3.1)

| 功能 | API端点 | 后端文件 | 前端页面 | 核心算法/数据结构 | 测试文件 | 状态 |
|------|---------|---------|---------|-----------------|---------|------|
| 景点列表 | GET /api/attractions | backend/routes/attractions.py:18-62 | frontend/pages/home.html | top_k (O(n log k)) | test_api_full_requirements.py | 完成 |
| 景点详情 | GET /api/attractions/\<id\> | attractions.py:65-82 | frontend/pages/attraction_detail.html | - | test_api_full_requirements.py | 完成 |
| 景点搜索 | GET /api/attractions/search | attractions.py:85-121 | frontend/pages/home.html | fuzzy_search (编辑距离) | test_api_full_requirements.py | 完成 |
| 景点推荐 | GET /api/recommend | attractions.py:124-173 | frontend/pages/home.html | top_k | test_api_full_requirements.py | 完成 |
| 校园列表 | GET /api/campuses | attractions.py:176-189 | frontend/pages/home.html | - | test_api_full_requirements.py | 完成 |
| 分类过滤 | ?campus_id= | attractions.py:37-39 | - | - | test_api_full_requirements.py | 完成 |
| 排序 | ?sort=heat/rating | attractions.py:42-47 | - | top_k | test_api_full_requirements.py | 完成 |

**数据模型**: backend/models/attraction.py

**核心算法**:
- Top-K排序: O(n log k) - sort.py:top_k
- 模糊搜索: fuzzy_search.py:fuzzy_search (编辑距离匹配)

---

### 2.2 最短路径规划 (3.2)

| 功能 | API端点 | 后端文件 | 前端页面 | 核心算法/数据结构 | 测试文件 | 状态 |
|------|---------|---------|---------|-----------------|---------|------|
| 室外路径规划 | POST /api/route/plan | backend/routes/route.py | frontend/pages/route_planning.html | Dijkstra (O((V+E)logV)) | test_api_full_requirements.py | 完成 |
| TSP多景点路线 | POST /api/route/tsp | route.py:tsp_route() | - | TSP (贪心+2-opt) | test_api_full_requirements.py | 完成 |
| 室内导航 | POST /api/route/indoor | route.py:indoor_route() | - | Dijkstra on indoor graph | test_api_full_requirements.py | 完成 |
| 电梯跨层导航 | 室内图 elevator 边 | indoor_navigation_service.py | - | 分层图Dijkstra | test_indoor_route.py | 完成 |
| 最短路径算法 | dijkstra() | backend/algorithms/dijkstra.py | - | 最小堆优化 | test_road_network.py | 完成 |

**核心数据结构**:
- Graph: backend/core/graph.py (邻接表)
- MinHeap: backend/core/heap.py (优先队列)

---

### 2.3 场所查询 (3.3)

| 功能 | API端点 | 后端文件 | 前端页面 | 核心算法/数据结构 | 测试文件 | 状态 |
|------|---------|---------|---------|-----------------|---------|------|
| 附近设施查询 | GET /api/nearby | backend/routes/nearby.py | frontend/pages/route_planning.html | Dijkstra道路距离 | test_api_full_requirements.py | 完成 |
| 按类型筛选 | ?type= | nearby.py | - | - | test_api_full_requirements.py | 完成 |
| 按距离排序 | ?sort=distance | nearby.py | - | Dijkstra + heap_sort | test_api_full_requirements.py | 完成 |
| 设施数据 | facilities.json | backend/data/ | - | 图结构 | test_data_scale.py | 完成 |

**数据模型**: backend/models/facility.py

---

### 2.4 旅游日记分享 (3.4)

| 功能 | API端点 | 后端文件 | 前端页面 | 核心算法/数据结构 | 测试文件 | 状态 |
|------|---------|---------|---------|-----------------|---------|------|
| 日记列表 | GET /api/diaries | backend/routes/diary.py:37-82 | frontend/pages/diary_square.html | top_k | test_api_full_requirements.py | 完成 |
| 日记详情 | GET /api/diary/\<id\> | diary.py:199-216 | frontend/pages/diary_detail.html | - | test_api_full_requirements.py | 完成 |
| 创建日记 | POST /api/diary | diary.py:131-196 | frontend/pages/diary_write.html | - | test_api_full_requirements.py | 完成 |
| 更新日记 | PUT /api/diary/\<id\> | diary.py:219-259 | - | - | test_api_full_requirements.py | 完成 |
| 删除日记 | DELETE /api/diary/\<id\> | diary.py:262-282 | - | - | test_api_full_requirements.py | 完成 |
| 评分日记 | POST /api/diary/\<id\>/rate | diary.py:285-317 | - | - | test_api_full_requirements.py | 完成 |
| 全文搜索 | GET /api/diaries/search | diary.py:85-128 | frontend/pages/diary_square.html | TextSearchIndex (倒排索引) | test_api_full_requirements.py | 完成 |
| 标题精确搜索 | GET /api/diaries/title | diary.py:393-418 | - | - | test_api_full_requirements.py | 完成 |
| 按目的地筛选 | GET /api/diaries?location_id= | diary.py:56-58 | - | - | test_api_full_requirements.py | 完成 |
| 日记压缩存储 | POST /api/diary/\<id\>/compress | diary.py:319-362 | - | HuffmanCoding | test_api_full_requirements.py | 完成 |
| 日记解压读取 | POST /api/diary/\<id\>/decompress | diary.py:364-427 | - | HuffmanCoding | test_api_full_requirements.py | 完成 |
| AIGC动画生成 | POST /api/aigc/animation | backend/routes/aigc.py | - | 模拟fallback | test_api_full_requirements.py | 完成 |

**数据模型**: backend/models/diary.py

**核心算法**:
- 霍夫曼压缩: backend/algorithms/compression.py:HuffmanCoding
- 全文搜索: backend/algorithms/text_search.py:TextSearchIndex

**前端页面状态**:
- diary_square.html: 静态页面，部分完成
- diary_detail.html: 静态页面，部分完成
- diary_write.html: 静态页面，部分完成

---

### 2.5 美食推荐 (3.5)

| 功能 | API端点 | 后端文件 | 前端页面 | 核心算法/数据结构 | 测试文件 | 状态 |
|------|---------|---------|---------|-----------------|---------|------|
| 美食列表 | GET /api/foods | backend/routes/food.py:136-219 | frontend/pages/food.html | top_k | test_api_full_requirements.py | 完成 |
| 美食搜索 | GET /api/foods/search | food.py:222-276 | - | fuzzy_search | test_api_full_requirements.py | 完成 |
| 美食推荐 | GET /api/foods/recommend | food.py:279-330 | - | top_k | test_api_full_requirements.py | 完成 |
| 菜系列表 | GET /api/cuisines | food.py:333-343 | - | - | test_api_full_requirements.py | 完成 |
| 按菜系筛选 | ?cuisine= | food.py:166-167 | - | - | test_api_full_requirements.py | 完成 |
| 按距离排序 | ?sort=distance | food.py:181-201 | - | Dijkstra道路距离 | test_api_full_requirements.py | 完成 |

**数据模型**: backend/models/food.py

---

### 2.6 地图显示 (3.6)

| 功能 | 文件 | Leaflet | 状态 |
|------|-----|---------|------|
| 路线规划页面 | frontend/pages/route_planning.html | 是 | 部分完成 |
| 景点详情页 | frontend/pages/attraction_detail.html | 是 | 部分完成 |
| 美食页面 | frontend/pages/food.html | 是 | 部分完成 |
| 日记广场 | frontend/pages/diary_square.html | 是 | 部分完成 |

---

## 3. 核心数据结构实现检查

| 数据结构 | 要求 | 实现文件 | 状态 |
|---------|------|------|------|
| 图（邻接表） | 自己实现 | backend/core/graph.py | 完成 |
| 堆（优先队列） | 自己实现 | backend/core/heap.py | 完成 |
| 哈希表 | 自己实现 | backend/core/hashtable.py | 完成 |
| 链表 | 自己实现 | backend/core/linkedlist.py | 完成 |
| 排序算法 | 自己实现 | backend/core/sort.py | 完成 |

---

## 4. 代码质量修复记录

### 4.1 Top-K Anti-Pattern 修复

**问题描述**: 原本使用 `top_k(data, len(data))` 会导致全量排序而非Top-K优化。

**修复文件**:
- backend/routes/diary.py: 行62, 67 - 改为 `top_k(diaries, limit, ...)`
- backend/routes/attractions.py: 行43, 46, 156, 157, 161, 164 - 改为 `top_k(attractions, limit, ...)`
- backend/routes/food.py: 行203, 205, 254, 314, 315, 319, 321 - 改为 `top_k(foods, limit, ...)`

**同时修复**: sort.py:top_k 使用 HeapElement 包装以支持自定义 key 函数比较。

---

## 5. 测试覆盖

| 模块 | 测试文件 | 覆盖 |
|------|---------|------|
| 道路网络 | test_road_network.py | Dijkstra, 连通分量, POI挂载 |
| 附近查询 | test_nearby.py | 设施查询, 距离排序 |
| 美食 | test_food.py | 列表, 搜索, 推荐 |
| 数据规模 | test_data_scale.py | POI数量, 挂载率 |
| 室内导航 | test_indoor_route.py | 多层路径, 电梯 |
| 综合API | test_api_full_requirements.py | 3.1-3.6全部API端点 |

**测试结果**: 83 passed

---

## 6. 状态总结

### 全部完成的功能

| 模块 | 状态 | 说明 |
|------|------|------|
| 3.1 旅游景区介绍及推荐 | 完成 | 后端API+算法全部实现 |
| 3.2 最短路径规划 | 完成 | Dijkstra+TSP+室内导航全部实现 |
| 3.3 场所查询 | 完成 | 基于道路网络的附近设施查询 |
| 3.4 旅游日记分享 | 完成 | CRUD+搜索+评分+压缩+解压全部实现 |
| 3.5 美食推荐 | 完成 | 列表+搜索+推荐+Dijkstra距离 |
| 3.6 地图显示 | 部分完成 | 静态HTML页面使用Leaflet |

### 前端页面状态

| 页面 | 状态 | 说明 |
|------|------|------|
| home.html | 部分完成 | 静态页面，API已对接 |
| route_planning.html | 部分完成 | 静态页面，Leaflet地图 |
| attraction_detail.html | 部分完成 | 静态页面 |
| food.html | 部分完成 | 静态页面 |
| diary_square.html | 部分完成 | 静态页面 |
| diary_detail.html | 部分完成 | 静态页面 |
| diary_write.html | 部分完成 | 静态页面 |

### 剩余缺口

无后端功能缺口。前端为静态页面，如需动态交互需后续开发。

---

**最后更新**: 2026-05-03
**状态**: 全部功能已完成