# TripMind 文件清理报告

## 1. 当前项目根目录结构

```
/data/xjr/TripMind/
├── 4.19                     # 旧文件（2019年）
├── before4.19/              # 旧文件（2019年）
├── beijing_geom.json       # 地理数据文件（被git跟踪）
├── beijing_ways.json       # 地理数据文件（被git跟踪）
├── claude_code_个性化旅游系统_执行说明书.md  # Claude执行说明
├── C-log.txt               # C的日志文件
├── T-log.txt               # T的日志文件
├── 交接文档.md             # 交接文档
├── 课程设计方案.md        # 课程设计文档
├── 课程设计方案.pdf       # PDF版本
├── 课程设计说明书.md       # 课程设计说明书
├── 课程设计说明书.pdf      # PDF版本
├── 数据结构课程设计-2026-更新补充.pdf  # 课程参考PDF
├── 数据结构课程设计-2026.pdf  # 旧版课程PDF
├── backend/                # 后端代码 ✓
├── frontend/               # 前端代码 ✓
├── scripts/                # 脚本 ✓
├── tests/                  # 测试 ✓
├── docs/                   # 文档 ✓
├── TRIPMIND/               # 旧gitlink目录 ⚠️
├── .git/                   # Git仓库
├── .gitignore              # Git忽略配置
├── README.md               # 项目说明
├── PRD.md                  # 产品需求文档
├── SPEC.md                 # 规格说明书
└── requirements.txt         # Python依赖
```

## 2. 核心代码（必须保留）

| 目录 | 说明 | 状态 |
|------|------|------|
| backend/core/ | 核心数据结构（Graph, Heap, HashTable, LinkedList, Sort） | ✓ 有效 |
| backend/algorithms/ | 核心算法（Dijkstra, TSP, FuzzySearch, TopK） | ✓ 有效 |
| backend/models/ | 数据模型 | ✓ 有效 |
| backend/routes/ | API路由 | ✓ 有效 |
| backend/services/ | 服务层 | ✓ 有效 |
| backend/data/ | 数据存储（含indoor_graphs.json） | ✓ 有效 |
| frontend/ | 前端页面 | ✓ 有效 |

## 3. 有效数据文件（必须保留）

| 文件 | 说明 | 状态 |
|------|------|------|
| backend/data/indoor_graphs.json | 室内导航图数据（2个建筑） | ✓ 有效 |
| backend/data/attractions.json | 景点数据（200条） | ✓ 有效 |
| backend/data/buildings.json | 建筑数据（20条） | ✓ 有效 |
| backend/data/facilities.json | 设施数据（50条） | ✓ 有效 |
| backend/data/foods.json | 美食数据（50条） | ✓ 有效 |
| backend/data/diaries.json | 日记数据（30条） | ✓ 有效 |
| backend/data/users.json | 用户数据（10条） | ✓ 有效 |
| backend/data/roads.json | 道路数据（51317条） | ✓ 有效 |
| backend/data/beijing_road_nodes.json | 道路节点数据（24567条） | ✓ 有效 |

## 4. 有效测试（必须保留）

| 文件 | 说明 | 状态 |
|------|------|------|
| tests/test_road_network.py | 道路网络集成测试 | ✓ 有效 |
| tests/test_nearby.py | nearby.py功能测试 | ✓ 有效 |
| tests/test_food.py | food.py功能测试 | ✓ 有效 |
| tests/test_data_scale.py | 数据规模测试 | ✓ 有效 |
| tests/test_indoor_route.py | 室内导航测试 | ✓ 有效 |

## 5. 有效脚本（必须保留）

| 文件 | 说明 | 状态 |
|------|------|------|
| scripts/connect_poi_to_road_network.py | POI挂载脚本 | ✓ 有效 |
| scripts/supplement_data.py | 数据补齐脚本 | ✓ 有效 |
| scripts/validate_data.py | 数据验证脚本 | ✓ 有效 |
| scripts/validate_road_network.py | 道路网络验证脚本 | ✓ 有效 |

## 6. 有效文档（必须保留）

| 文件 | 说明 | 状态 |
|------|------|------|
| docs/data_scale_report.md | 数据规模报告 | ✓ 有效 |
| docs/road_network_integration.md | 道路网络集成文档 | ✓ 有效 |
| docs/indoor_navigation_design.md | 室内导航设计文档 | ✓ 有效 |

## 7. 待补充文档

以下文档在规范要求中提到但尚未创建：

| 文件 | 说明 | 状态 |
|------|------|------|
| docs/algorithm_analysis.md | 算法分析文档 | 待补充 |
| docs/demo_script.md | 演示脚本 | 待补充 |
| docs/defense_questions.md | 答辩问题清单 | 待补充 |
| docs/requirement_traceability_matrix.md | 需求追溯矩阵 | 待补充 |

## 8. 疑似重复/过期文件

| 文件/目录 | 说明 | 建议 |
|----------|------|------|
| TRIPMIND/ | 旧gitlink目录，指向commit 10fe6c1 | 归档到 archive/TRIPMIND_old/ |
| 4.19 | 2019年旧文件 | 归档到 archive/old_docs/ |
| before4.19/ | 2019年旧文件 | 归档到 archive/old_docs/ |
| 数据结构课程设计-2026.pdf | 旧版课程PDF | 归档到 archive/old_docs/ |
| C-log.txt, T-log.txt | 个人日志文件 | 删除 |
| claude_code_个性化旅游系统_执行说明书.md | 执行说明文档 | 归档到 archive/old_docs/ |

## 9. __pycache__ 目录

| 目录 | 建议 |
|------|------|
| /data/xjr/TripMind/backend/*/__pycache__ | 已加入.gitignore，可直接删除 |
| /data/xjr/TripMind/TRIPMIND/TripMind/backend/*/__pycache__ | 直接删除整个目录 |

## 10. 建议删除列表

1. **C-log.txt, T-log.txt** - 个人日志，无项目价值
2. **TRIPMIND/TripMind/** 下所有 __pycache__ 目录 - 临时缓存

## 11. 建议归档列表

创建 archive/ 目录：

```
archive/
├── old_docs/
│   ├── 4.19
│   ├── before4.19/
│   ├── 数据结构课程设计-2026.pdf
│   ├── claude_code_个性化旅游系统_执行说明书.md
│   └── 交接文档.md
├── TRIPMIND_old/
│   └── TRIPMIND/TripMind/  (整个旧gitlink目录)
└── data_backup/
    └── (空，暂无备份文件)
```

## 12. 建议修改列表

1. **README.md** - 可补充室内导航说明
2. **.gitignore** - 已基本完整，可补充 archive/data_backup/*.tmp

## 13. 旧目录内容检查

### TRIPMIND/TripMind/ 内容分析

该目录是被git跟踪为gitlink的旧目录，指向commit 10fe6c1。

**目录内容**：
- backend/ (旧版本，缺少indoor_navigation_service.py)
- frontend/ (旧版本)
- docs/ (旧版本，缺少indoor_navigation_design.md)
- tests/ (旧版本，缺少test_indoor_route.py)
- scripts/ (内容与当前仓库相同)
- 各种.md/pdf文件 (与当前仓库根目录重复)

**与当前仓库的差异**：
- backend/ - 缺少indoor_navigation_service.py
- docs/ - 缺少indoor_navigation_design.md
- tests/ - 缺少test_indoor_route.py
- scripts/ - 内容相同

**结论**：TRIPMIND/TripMind/ 是旧版副本，无有效差异，建议归档。

## 14. .gitignore 检查

当前 .gitignore 内容：
```
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
*.egg-info/

# 不排除 data 目录下的 json 文件
backend/data/*.json

# 前端
node_modules/
dist/

# IDE
.vscode/
.idea/

# 系统
.DS_Store
Thumbs.db

# 截图和临时文件
*.jpg
*.png
convert_to_pdf.py

# 课程PDF（不上传但本地保留）
*.pdf
```

**建议补充**：
- archive/
- *.log
- .env
- .venv/
- venv/

## 15. 清理操作计划

1. 创建 archive/ 目录
2. 移动旧文档到 archive/old_docs/
3. 移动旧gitlink目录到 archive/TRIPMIND_old/
4. 删除 __pycache__ 目录
5. 删除 C-log.txt, T-log.txt
6. 更新 .gitignore
7. 更新 README.md（如需要）
8. 运行测试验证

## 16. 风险评估

| 操作 | 风险 | 缓解措施 |
|------|------|---------|
| 归档TRIPMIND/ | 可能丢失未迁移文件 | 已确认所有有效文件已复制到正确位置 |
| 删除__pycache__ | 无风险，是临时缓存 | 不影响代码 |
| 删除日志文件 | 无风险，是个人文件 | 已确认无项目价值 |

---
生成时间：2026-05-03