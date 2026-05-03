# 室内导航设计文档

## 1. 概述

室内导航是 TripMind 项目的重要组成部分，支持在建筑物内部进行路径规划。用户可以查询从建筑入口到任意房间的最短路径，支持多楼层导航。

### 1.1 课程要求对应

| 要求 | 实现 |
|------|------|
| 模拟教学楼/博物馆等建筑内部结构 | indoor_graphs.json 定义2个建筑（教学楼A、图书馆） |
| 支持大门到电梯导航 | 起点支持 "gate"/"entrance"，终点支持 "elevator" |
| 支持楼层间电梯导航 | 电梯节点跨层连接，时间固定15秒 |
| 支持楼层内到房间导航 | 走廊连接房间节点，支持room_access类型边 |
| 使用图结构 + Dijkstra | 使用Graph类 + dijkstra算法 |
| 能通过API和测试演示 | POST /api/route/indoor 已实现 |

### 1.2 为什么室内导航建模为分层图

室内建筑天然具有楼层结构，每层都有相同的功能区域（入口、走廊、房间、电梯）。使用分层图建模：

- **同一楼层**：节点通过走廊边(corridor)和房间访问边(room_access)连接
- **跨楼层**：通过电梯节点(elevator)连接，电梯边的时间固定（不考虑物理距离）

这种建模方式既反映了建筑的实际结构，又简化了跨楼层路径的计算。

## 2. 数据结构

### 2.1 节点设计

室内节点包含以下类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| entrance | 建筑入口 | BLD_001_F1_entrance |
| hall | 大厅/电梯厅 | BLD_001_F1_hall |
| elevator | 电梯节点 | BLD_001_F1_elevator |
| corridor | 走廊节点 | BLD_001_F1_corridor |
| room | 房间节点 | BLD_001_F1_room_101 |

节点ID格式：`{building_id}_F{floor}_{type}_{name}`

### 2.2 边设计

| 边类型 | 连接 | distance | time | 说明 |
|--------|------|----------|------|------|
| corridor | 同层相邻节点 | 8-20m | 6-15s | 走廊连接 |
| room_access | 走廊到房间 | 12-18m | 10-14s | 房间访问 |
| elevator | 跨层电梯节点 | 0m | 15s | 固定时间 |

### 2.3 电梯跨层边表示

电梯节点在各楼层都有实例（如 BLD_001_F1_elevator、BLD_001_F2_elevator），它们之间用 elevator 类型的边连接：

```json
{
  "from": "BLD_001_F1_elevator",
  "to": "BLD_001_F2_elevator",
  "distance": 0,
  "time": 15,
  "type": "elevator"
}
```

电梯边的 distance=0 表示物理距离为0，time=15 表示电梯开关门和运行时间为15秒。

### 2.4 大门到电梯、楼层间电梯、楼层内到房间的路径体现

以 `gate -> room_301` 为例，路径为：

```
一层大门 -> 一层大厅 -> 一层电梯 -> 二层电梯 -> 三层电梯 -> 三层大厅 -> 三层走廊 -> 301教室
```

- **大门到一层电梯**：穿过一层大厅到达一层电梯
- **楼层间电梯**：从一层电梯到三层电梯（经过二层）
- **三层内到房间**：从三层电梯到三层大厅，再到走廊，最后到301教室

## 3. 算法实现

### 3.1 Dijkstra 计算流程

```python
def plan_indoor_route(building_id, start, end, strategy='time'):
    # 1. 加载建筑数据，构建室内图
    building, graph = get_building_graph(building_id)

    # 2. 解析起点和终点
    start_node = resolve_indoor_node(building, start)  # "gate" -> "BLD_001_F1_entrance"
    end_node = resolve_indoor_node(building, end)    # "room_301" -> "BLD_001_F3_room_301"

    # 3. 使用Dijkstra计算最短路径
    weight = 'time' if strategy == 'time' else 'distance'
    result = dijkstra(graph, start_node, end_node, weight=weight)

    # 4. 重建路径，计算总距离和总时间
    path = result['path']
    total_distance = sum(graph.get_edge(path[i], path[i+1])['distance'] for i in range(len(path)-1))
    total_time = sum(graph.get_edge(path[i], path[i+1])['time'] for i in range(len(path)-1))

    return {
        'success': True,
        'path': path,
        'total_distance': total_distance,
        'total_time': total_time,
        'algorithm': 'Dijkstra on indoor graph'
    }
```

### 3.2 节点解析逻辑

```python
def resolve_indoor_node(building, user_input):
    # "gate" -> 主入口
    # "elevator" -> 一楼电梯
    # "room_101" -> 101房间
    # "101" -> 101房间
```

## 4. API 接口

### 4.1 室内导航

**POST** `/api/route/indoor`

**请求体**：
```json
{
  "building_id": "BLD_001",
  "start": "gate",
  "end": "room_301",
  "strategy": "time"
}
```

**响应**：
```json
{
  "code": 200,
  "data": {
    "success": true,
    "building_id": "BLD_001",
    "building_name": "教学楼A",
    "start": "gate",
    "end": "room_301",
    "strategy": "time",
    "path": [
      "BLD_001_F1_entrance",
      "BLD_001_F1_hall",
      "BLD_001_F1_elevator",
      "BLD_001_F2_elevator",
      "BLD_001_F3_elevator",
      "BLD_001_F3_hall",
      "BLD_001_F3_corridor",
      "BLD_001_F3_room_301"
    ],
    "path_nodes": [
      {"node_id": "BLD_001_F1_entrance", "name": "一层大门", "floor": 1, "type": "entrance"},
      {"node_id": "BLD_001_F1_hall", "name": "一层大厅", "floor": 1, "type": "hall"},
      {"node_id": "BLD_001_F1_elevator", "name": "一层电梯", "floor": 1, "type": "elevator"},
      {"node_id": "BLD_001_F2_elevator", "name": "二层电梯", "floor": 2, "type": "elevator"},
      {"node_id": "BLD_001_F3_elevator", "name": "三层电梯", "floor": 3, "type": "elevator"},
      {"node_id": "BLD_001_F3_hall", "name": "三层大厅", "floor": 3, "type": "hall"},
      {"node_id": "BLD_001_F3_corridor", "name": "三层走廊", "floor": 3, "type": "corridor"},
      {"node_id": "BLD_001_F3_room_301", "name": "301教室", "floor": 3, "type": "room"}
    ],
    "total_distance": 55,
    "total_time": 74,
    "algorithm": "Dijkstra on indoor graph"
  },
  "message": "success"
}
```

### 4.2 起点/终点支持格式

| 输入 | 解析结果 |
|------|----------|
| "gate" | 主入口节点 |
| "entrance" | 主入口节点 |
| "elevator" | 一楼电梯节点 |
| "room_101" | 101房间节点 |
| "101" | 101房间节点 |
| "301教室" | 301教室节点 |
| 完整node_id | 直接使用 |

## 5. 测试说明

### 5.1 测试用例

```bash
python tests/test_indoor_route.py
```

测试覆盖：

1. indoor_graphs.json 存在且至少2个建筑
2. 每个建筑有 entrance、elevator、room、edge
3. 大门到同层房间可达
4. 大门到高楼层房间可达
5. 高楼层房间路径必须经过电梯节点
6. 路径不是固定假路径（不同目标产生不同路径）
7. 不存在 building_id 时返回错误
8. 不存在 room 时返回错误
9. strategy=time 和 strategy=distance 均可运行
10. 返回结果包含 total_distance、total_time、algorithm

### 5.2 测试结果

```
==================================================
室内导航测试
==================================================

[测试] indoor_graphs.json 存在且2个建筑
  建筑数量: 2
    BLD_001: 教学楼A
    BLD_002: 图书馆
  ✓ 通过

[测试] 同层导航
  gate -> room_101: 成功
    路径: ['一层大门', '一层大厅', '一层走廊', '101教室']
    距离: 35m
    时间: 28s
  ✓ 通过

[测试] 多层导航
  gate -> room_301: 成功
    路径: ['一层大门', '一层大厅', '一层电梯', '二层电梯', '三层电梯', '三层大厅', '三层走廊', '301教室']
    距离: 55m
    时间: 74s
  ✓ 通过
```

## 6. 复杂度分析

| 操作 | 时间复杂度 | 说明 |
|------|-----------|------|
| 构建室内图 | O(V + E) | V=节点数, E=边数 |
| Dijkstra最短路径 | O((V+E) log V) | 使用最小堆优化 |
| 节点解析 | O(V) | 线性扫描节点列表 |

室内图规模：
- 教学楼A：16节点，15边
- 图书馆：17节点，16边

对于这种规模，Dijkstra算法可以在毫秒级完成路径计算。

## 7. 文件清单

```
backend/
├── data/
│   └── indoor_graphs.json      # 室内图数据（2个建筑）
├── services/
│   └── indoor_navigation_service.py  # 室内导航服务
└── routes/
    └── route.py               # /api/route/indoor 端点

tests/
└── test_indoor_route.py      # 室内导航测试

docs/
└── indoor_navigation_design.md  # 本文档
```

## 8. 与室外道路网络的区别

| 特性 | 室外道路网络 | 室内导航 |
|------|-------------|---------|
| 节点数量 | 24,567 | ~17 |
| 边数量 | 51,317 | ~16 |
| 边的权重 | 实际距离 | corridor/room_access按距离，elevator按固定时间 |
| 跨层 | 不需要 | 通过电梯节点 |
| 路径算法 | Dijkstra | Dijkstra |

室内导航与室外道路网络使用相同的Dijkstra算法，但边权重的计算方式不同。