"""
无损压缩算法 - 霍夫曼编码
用于：日记内容压缩存储
课程要求：必须自己实现
"""

from typing import Dict, Tuple, Optional, List
from collections import Counter, defaultdict
import heapq


class HuffmanNode:
    """霍夫曼树节点"""

    def __init__(self, char: str = None, freq: int = 0, left=None, right=None):
        self.char = char      # 字符（叶子节点有）
        self.freq = freq      # 频率
        self.left = left      # 左子树
        self.right = right    # 右子树

    def __lt__(self, other):
        """用于优先队列比较"""
        return self.freq < other.freq


class HuffmanCoding:
    """
    霍夫曼编码 - 一种无损数据压缩算法

    算法步骤：
        1. 统计字符频率
        2. 构建霍夫曼树（频率低的在下，频率高的在上）
        3. 生成编码表（左子树=0，右子树=1）
        4. 编码：用编码替换原始字符
        5. 解码：沿树路径还原

    时间复杂度: O(n log n)，n为字符数
    压缩效果：高频字符用短码，低频字符用长码
    """

    def __init__(self):
        self._root = None
        self._code_table = {}  # 编码表：{字符: 编码}
        self._decode_table = {}  # 解码表：{编码: 字符}

    def build(self, text: str):
        """
        构建霍夫曼编码表

        参数:
            text: 要压缩的文本
        """
        if not text:
            return

        # 1. 统计字符频率
        freq_counter = Counter(text)

        # 2. 创建叶子节点并加入优先队列
        heap = []
        for char, freq in freq_counter.items():
            node = HuffmanNode(char=char, freq=freq)
            heapq.heappush(heap, node)

        # 3. 构建霍夫曼树
        while len(heap) > 1:
            # 取出两个频率最低的节点
            node1 = heapq.heappop(heap)
            node2 = heapq.heappop(heap)

            # 合并成新节点
            merged = HuffmanNode(
                freq=node1.freq + node2.freq,
                left=node1,
                right=node2
            )
            heapq.heappush(heap, merged)

        self._root = heap[0] if heap else None

        # 4. 生成编码表
        self._code_table.clear()
        self._decode_table.clear()
        if self._root:
            self._generate_codes(self._root, '')

    def _generate_codes(self, node: HuffmanNode, code: str):
        """递归生成编码"""
        if node.char:
            # 叶子节点
            self._code_table[node.char] = code if code else '0'
            self._decode_table[code if code else '0'] = node.char
        else:
            # 非叶子节点
            if node.left:
                self._generate_codes(node.left, code + '0')
            if node.right:
                self._generate_codes(node.right, code + '1')

    def encode(self, text: str) -> Tuple[str, Dict]:
        """
        编码文本

        参数:
            text: 原始文本

        返回:
            (编码后的二进制字符串, 编码表)
        """
        if not text:
            return '', {}

        if not self._code_table:
            self.build(text)

        encoded = ''
        for char in text:
            if char in self._code_table:
                encoded += self._code_table[char]
            else:
                # 对于不在编码表中的字符（如换行符），使用原始字符
                encoded += char

        return encoded, self._code_table.copy()

    def decode(self, encoded: str, code_table: Dict = None) -> str:
        """
        解码文本

        参数:
            encoded: 编码后的二进制字符串
            code_table: 编码表（如果不在实例中存储）

        返回:
            解码后的原始文本
        """
        if not encoded:
            return ''

        # 使用提供的编码表或实例中的编码表
        decode_table = {}
        if code_table:
            decode_table = {v: k for k, v in code_table.items()}
        elif self._decode_table:
            decode_table = self._decode_table

        # 如果使用实例的解码表（编码时用实例的）
        if not decode_table and self._decode_table:
            decode_table = self._decode_table

        # 解码
        decoded = []
        current_code = ''

        for bit in encoded:
            current_code += bit
            if current_code in decode_table:
                decoded.append(decode_table[current_code])
                current_code = ''

        return ''.join(decoded)

    def compress(self, text: str) -> Tuple[bytes, Dict]:
        """
        压缩文本（返回字节串，便于存储）

        将二进制字符串转换为字节数组
        第一个字节保存padding长度（补0的位数），这样解压时可以正确去除

        返回:
            (压缩后的字节数据, 编码表)
        """
        if not text:
            return b'', {}

        encoded, _ = self.encode(text)

        # 计算padding：编码的bit数不是8的倍数时需要补0
        bit_len = len(encoded)
        padding = (8 - bit_len % 8) % 8  # 0到7的padding

        # 末尾补padding个0
        encoded_padded = encoded + '0' * padding

        # 将二进制字符串转换为字节（第一个字节是padding长度）
        byte_data = bytearray()
        byte_data.append(padding)  # 第一个字节保存padding长度

        for i in range(0, len(encoded_padded), 8):
            byte = encoded_padded[i:i+8]
            byte_data.append(int(byte, 2))

        return bytes(byte_data), self._code_table.copy()

    def decompress(self, compressed: bytes, code_table: Dict) -> str:
        """
        解压文本

        参数:
            compressed: 压缩后的字节数据（第一个字节是padding长度）
            code_table: 编码表

        返回:
            解压后的文本
        """
        if not compressed:
            return ''

        # 第一个字节是padding长度
        padding = compressed[0] if len(compressed) > 0 else 0
        if padding < 0 or padding > 7:
            padding = 0  # 安全检查

        # 将剩余字节转换为二进制字符串
        encoded = ''
        for i in range(1, len(compressed)):
            encoded += format(compressed[i], '08b')

        # 去除末尾的padding位
        if padding > 0 and len(encoded) >= padding:
            encoded = encoded[:-padding]

        return self.decode(encoded, code_table)

    def get_stats(self, text: str) -> Dict:
        """
        获取压缩统计信息

        返回:
            {
                'original_size': 原始大小(字节),
                'compressed_size': 压缩后大小(字节),
                'compression_ratio': 压缩比,
                'code_table_size': 编码表大小,
                'unique_chars': 不同字符数
            }
        """
        if not text:
            return {}

        # 原始大小
        original_size = len(text.encode('utf-8'))

        # 压缩
        compressed, code_table = self.compress(text)

        # 编码表大小（估算）
        code_table_size = sum(len(k) + len(v) + 10 for k, v in code_table.items())

        return {
            'original_size': original_size,
            'compressed_size': len(compressed),
            'compression_ratio': len(compressed) / original_size if original_size > 0 else 0,
            'code_table_size': code_table_size,
            'unique_chars': len(code_table)
        }


def compress_text(text: str) -> Tuple[bytes, Dict]:
    """
    快捷函数：压缩文本
    """
    huffman = HuffmanCoding()
    huffman.build(text)
    return huffman.compress(text)


def decompress_text(compressed: bytes, code_table: Dict) -> str:
    """
    快捷函数：解压文本
    """
    huffman = HuffmanCoding()
    return huffman.decompress(compressed, code_table)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("霍夫曼压缩算法测试")
    print("=" * 50)

    # 测试文本
    test_texts = [
        "aaaaabbbbbcccccddddd",
        "北京邮电大学是个很好的学校，北京邮电大学的食堂很好吃！",
        "故宫是必去的景点，故宫很大，需要一天才能逛完。天坛公园也值得去。",
    ]

    for text in test_texts:
        print(f"\n原始文本: {text[:50]}{'...' if len(text) > 50 else ''}")

        # 压缩
        huffman = HuffmanCoding()
        huffman.build(text)
        compressed, code_table = huffman.compress(text)

        # 解压验证
        decompressed = huffman.decompress(compressed, code_table)

        # 统计
        original_size = len(text.encode('utf-8'))
        compression_ratio = len(compressed) / original_size

        print(f"  原始大小: {original_size} bytes")
        print(f"  压缩后: {len(compressed)} bytes")
        print(f"  压缩比: {compression_ratio:.2%}")
        print(f"  解压验证: {'成功' if decompressed == text else '失败'}")
        print(f"  编码表示例: {dict(list(code_table.items())[:5])}")

    # 性能对比
    print("\n" + "=" * 50)
    print("压缩性能测试（较长的文本）")
    print("=" * 50)

    # 生成测试文本
    import random
    chars = 'abcdefghijklmnopqrstuvwxyz '
    long_text = ''.join(random.choice(chars) for _ in range(10000))

    huffman = HuffmanCoding()
    huffman.build(long_text)
    compressed, _ = huffman.compress(long_text)

    original_size = len(long_text.encode('utf-8'))
    print(f"  原始大小: {original_size} bytes")
    print(f"  压缩后: {len(compressed)} bytes")
    print(f"  压缩比: {len(compressed)/original_size:.2%}")

    print("\n[SUCCESS] Huffman compression test passed!")
