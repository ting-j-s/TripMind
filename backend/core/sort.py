"""
排序算法实现 - 自己动手实现，不用Python内置的sorted
这些是课程要求的"核心算法"，必须自己实现
"""

from .heap import MaxHeap, HeapElement


# ============================================================
# 快速排序 (Quick Sort)
# ============================================================

def quick_sort(arr, key=None, reverse=False):
    """
    快速排序 - O(n log n) 平均时间复杂度

    参数:
        arr: 要排序的列表
        key: 比较的键，如 lambda x: x['heat']
        reverse: 是否降序

    返回:
        排序后的新列表（不修改原列表）
    """
    if len(arr) <= 1:
        return list(arr)

    if key is None:
        key = lambda x: x

    # 选择基准（中间元素）
    pivot = arr[len(arr) // 2]
    pivot_val = key(pivot)

    # 分区
    left = []
    middle = []
    right = []

    for item in arr:
        item_val = key(item)
        if item_val < pivot_val:
            left.append(item)
        elif item_val > pivot_val:
            right.append(item)
        else:
            middle.append(item)

    # 递归排序
    result = []
    if reverse:
        result += quick_sort(right, key, reverse)
        result += middle
        result += quick_sort(left, key, reverse)
    else:
        result += quick_sort(left, key, reverse)
        result += middle
        result += quick_sort(right, key, reverse)

    return result


# ============================================================
# 堆排序 (Heap Sort)
# ============================================================

def heap_sort(arr, key=None, reverse=False):
    """
    堆排序 - O(n log n) 时间复杂度

    参数:
        arr: 要排序的列表
        key: 比较的键
        reverse: 是否降序

    返回:
        排序后的新列表
    """
    if len(arr) <= 1:
        return list(arr)

    if key is None:
        key = lambda x: x

    # 构建堆
    def sift_down(items, start, end):
        """向下调整"""
        while True:
            root = start
            left = 2 * root + 1
            right = 2 * root + 2

            if left > end:
                break

            # 找较小的子节点
            swap = left
            if right <= end:
                if key(items[right]) < key(items[left]):
                    swap = right

            if key(items[swap]) < key(items[root]):
                items[root], items[swap] = items[swap], items[root]
                root = swap
            else:
                break

    n = len(arr)
    items = list(arr)

    # 构建最大堆
    for start in range(n // 2 - 1, -1, -1):
        sift_down(items, start, n - 1)

    # 堆排序
    for end in range(n - 1, 0, -1):
        items[0], items[end] = items[end], items[0]
        sift_down(items, 0, end - 1)

    if reverse:
        items.reverse()

    return items


# ============================================================
# Top-K 问题（部分排序）
# ============================================================

def top_k(arr, k, key=None, reverse=True):
    """
    Top-K 问题 - 只找出前K个最大/最小的元素

    时间复杂度: O(n log k)
    适用于: n很大，k很小（如10000个中找前10个）

    参数:
        arr: 要处理的列表
        k: 需要找出的元素个数
        key: 比较的键
        reverse: True表示找最大的，False表示找最小的

    返回:
        前K个元素的列表（已排序）

    示例:
        top_k([5,3,8,1,9,2], k=3) -> [9, 8, 5]（最大的3个）
        top_k([5,3,8,1,9,2], k=3, reverse=False) -> [1, 2, 3]（最小的3个）
    """
    if k <= 0:
        return []
    if len(arr) <= k:
        result = heap_sort(arr, key, reverse)
        return result

    if key is None:
        key = lambda x: x

    # 使用最大堆找前K个最大元素
    # 或最小堆找前K个最小元素

    if reverse:
        # 找最大的K个 -> 用最大堆
        # 维护一个大小为K的堆，堆顶是堆中最小的
        heap = MaxHeap()
        for item in arr:
            if len(heap) < k:
                heap.push(HeapElement(item, key(item)))
            else:
                # 如果当前元素比堆顶大，则替换
                if key(item) > key(heap.peek().value):
                    heap.pop()
                    heap.push(HeapElement(item, key(item)))
    else:
        # 找最小的K个 -> 用最小堆
        from .heap import MinHeap
        heap = MinHeap()
        for item in arr:
            if len(heap) < k:
                heap.push(HeapElement(item, key(item)))
            else:
                if key(item) < key(heap.peek().value):
                    heap.pop()
                    heap.push(HeapElement(item, key(item)))

    # 堆中就是前K个，但顺序是乱的，需要排序
    result = []
    while not heap.is_empty():
        result.append(heap.pop().value)

    # 排序
    result = heap_sort(result, key, reverse)

    return result


# ============================================================
# 实用工具函数
# ============================================================

def sort_by_heat(items, reverse=True):
    """按热度排序（热度越高越靠前）"""
    return heap_sort(items, key=lambda x: x.get('heat', 0), reverse=reverse)


def sort_by_rating(items, reverse=True):
    """按评分排序"""
    return heap_sort(items, key=lambda x: x.get('rating', 0), reverse=reverse)


def sort_by_distance(items, reverse=False):
    """按距离排序（距离越近越靠前）"""
    return heap_sort(items, key=lambda x: x.get('distance', float('inf')), reverse=reverse)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("排序算法测试")
    print("=" * 50)

    # 测试数据
    test_data = [
        {"id": "A", "heat": 5000, "rating": 4.5},
        {"id": "B", "heat": 3000, "rating": 4.8},
        {"id": "C", "heat": 8000, "rating": 4.2},
        {"id": "D", "heat": 1000, "rating": 4.9},
        {"id": "E", "heat": 6000, "rating": 4.6},
    ]

    print("\n原始数据:")
    for item in test_data:
        print(f"  {item['id']}: heat={item['heat']}, rating={item['rating']}")

    # 测试快速排序
    print("\n快速排序（按热度降序）:")
    sorted_data = quick_sort(test_data, key=lambda x: x['heat'], reverse=True)
    for item in sorted_data:
        print(f"  {item['id']}: heat={item['heat']}")

    # 测试堆排序
    print("\n堆排序（按评分降序）:")
    sorted_data = heap_sort(test_data, key=lambda x: x['rating'], reverse=True)
    for item in sorted_data:
        print(f"  {item['id']}: rating={item['rating']}")

    # 测试Top-K
    print("\nTop-K 测试:")
    print(f"  热度前3名: {[item['id'] for item in top_k(test_data, k=3, key=lambda x: x['heat'])]}")
    print(f"  评分前2名: {[item['id'] for item in top_k(test_data, k=2, key=lambda x: x['rating'])]}")

    # Top-K性能对比
    print("\n" + "=" * 50)
    print("Top-K 性能对比（10000个元素中找前10）")
    print("=" * 50)

    import time
    large_data = [{"id": i, "value": i} for i in range(10000)]

    # 全量排序
    start = time.time()
    result1 = heap_sort(large_data, key=lambda x: x['value'], reverse=True)[:10]
    full_sort_time = time.time() - start

    # Top-K
    start = time.time()
    result2 = top_k(large_data, k=10, key=lambda x: x['value'], reverse=True)
    topk_time = time.time() - start

    print(f"  全量排序时间: {full_sort_time:.4f}秒")
    print(f"  Top-K时间: {topk_time:.4f}秒")
    print(f"  加速比: {full_sort_time/topk_time:.1f}倍")
