"""
歌词文本处理工具 - 核心处理逻辑
将 karaoke.add(...) 格式转换为纯歌词文本
"""

import re
import os
from typing import List, Tuple, Optional


class LyricProcessor:
    """歌词处理器"""
    
    def __init__(self):
        self.songname = None
        self.singer = None
        self.lyrics = []
    
    def parse_file(self, file_path: str, encoding: str = 'utf-8') -> bool:
        """
        解析歌词文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码（默认UTF-8）
        
        Returns:
            是否解析成功
        """
        try:
            # 尝试多种编码（包括日韩文编码）
            encodings = [
                encoding,           # 用户指定的编码
                'utf-8',            # UTF-8（最常用，支持所有Unicode字符）
                'utf-8-sig',        # UTF-8 with BOM
                'shift_jis',        # 日文编码（Windows常用）
                'euc-jp',           # 日文编码（Unix常用）
                'cp932',            # 日文编码（Windows扩展）
                'euc-kr',           # 韩文编码（Unix常用）
                'cp949',            # 韩文编码（Windows常用，扩展EUC-KR）
                'gbk',              # 中文编码（GBK）
                'gb2312',           # 中文编码（GB2312）
                'big5',             # 繁体中文编码
                'latin1',           # 西欧编码（fallback）
            ]
            content = None
            
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            if content is None:
                return False
            
            return self.parse_content(content)
        except Exception as e:
            print(f"解析文件失败: {e}")
            return False
    
    def parse_content(self, content: str) -> bool:
        """
        解析文件内容
        
        Args:
            content: 文件内容字符串
        
        Returns:
            是否解析成功
        """
        try:
            self.songname = None
            self.singer = None
            self.lyrics = []
            
            # 提取歌名
            songname_match = re.search(r"karaoke\.songname\s*:=\s*['\"](.*?)['\"]", content)
            if songname_match:
                self.songname = songname_match.group(1)
            
            # 提取歌手
            singer_match = re.search(r"karaoke\.singer\s*:=\s*['\"](.*?)['\"]", content)
            if singer_match:
                self.singer = singer_match.group(1)
            
            # 提取所有 karaoke.add 行
            # 使用改进的方法：匹配整个调用，然后智能解析参数
            # 这样可以正确处理字符串中包含引号的情况
            add_pattern = r"karaoke\.add\s*\((.*?)\);"
            add_matches = re.findall(add_pattern, content, re.DOTALL)
            
            for params_str in add_matches:
                # 解析参数：提取第三个参数（歌词文本）
                lyric_text = self._extract_third_param(params_str)
                if lyric_text:
                    # 去除中括号并清理文本
                    lyric_line = self._clean_lyric(lyric_text)
                    if lyric_line:
                        self.lyrics.append(lyric_line)
            
            return True
        except Exception as e:
            print(f"解析内容失败: {e}")
            return False
    
    def _extract_third_param(self, params_str: str) -> str:
        """
        从 karaoke.add 的参数字符串中提取第三个参数（歌词文本）
        正确处理字符串中包含引号的情况
        
        Args:
            params_str: 参数字符串，如 "'03:35.708', '03:37.420', '[I'll ]', '616'"
        
        Returns:
            第三个参数的内容（已去除外层引号）
        """
        params_str = params_str.strip()
        if not params_str:
            return ""
        
        # 使用更智能的方法：从右往左查找，找到第三个逗号分隔的参数
        # 但更简单的方法是：使用正则表达式匹配引号字符串，考虑转义
        
        # 方法：匹配引号字符串（支持单引号和双引号，考虑转义）
        # 正则表达式：匹配 '...' 或 "..."，其中引号内的引号需要转义（两个连续引号）
        quote_pattern = r"(?:'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\")"
        matches = re.findall(quote_pattern, params_str)
        
        # 如果找到至少3个参数，返回第三个
        if len(matches) >= 3:
            third_param = matches[2]
            # 去除外层引号
            if third_param.startswith("'") and third_param.endswith("'"):
                result = third_param[1:-1]
                # 处理转义的引号：两个连续的单引号变成一个单引号
                result = result.replace("''", "'")
                return result
            elif third_param.startswith('"') and third_param.endswith('"'):
                result = third_param[1:-1]
                # 处理转义的引号：两个连续的双引号变成一个双引号
                result = result.replace('""', '"')
                return result
        
        # 如果正则匹配失败，使用备用方法：手动解析
        # 这种情况通常发生在字符串格式不正确时
        return self._extract_third_param_fallback(params_str)
    
    def _extract_third_param_fallback(self, params_str: str) -> str:
        """
        备用方法：手动解析参数（当正则表达式失败时使用）
        尝试找到第三个逗号分隔的参数
        """
        # 简单方法：按逗号分割，但需要智能处理引号内的逗号
        params = []
        i = 0
        current_param = ""
        in_quotes = False
        quote_char = None
        
        while i < len(params_str):
            char = params_str[i]
            
            if char in ['"', "'"] and (i == 0 or params_str[i-1] != '\\'):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                    current_param += char
                elif char == quote_char:
                    # 检查是否是转义的引号
                    if i + 1 < len(params_str) and params_str[i + 1] == quote_char:
                        current_param += char + char
                        i += 1
                    else:
                        current_param += char
                        in_quotes = False
                        quote_char = None
                else:
                    current_param += char
            elif char == ',' and not in_quotes:
                params.append(current_param.strip())
                current_param = ""
            else:
                current_param += char
            
            i += 1
        
        if current_param.strip():
            params.append(current_param.strip())
        
        if len(params) >= 3:
            third = params[2].strip()
            # 去除引号
            if (third.startswith("'") and third.endswith("'")) or \
               (third.startswith('"') and third.endswith('"')):
                third = third[1:-1]
                third = third.replace("''", "'").replace('""', '"')
            return third
        
        return ""
    
    def _clean_lyric(self, text: str) -> str:
        """
        清理歌词文本：去除中括号和多余空格
        
        Args:
            text: 原始歌词文本
        
        Returns:
            清理后的歌词文本
        """
        # 去除中括号
        text = re.sub(r'\[([^\]]*)\]', r'\1', text)
        # 去除多余空格，但保留单词间的单个空格
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空格
        text = text.strip()
        return text
    
    def to_text(self, include_header: bool = True, single_line: bool = False) -> str:
        """
        转换为文本格式
        
        Args:
            include_header: 是否包含歌名和歌手信息
            single_line: 是否输出为单行（空格分隔）
        
        Returns:
            格式化后的文本
        """
        lines = []
        
        # 添加头部信息
        if include_header and (self.songname or self.singer):
            header_parts = []
            if self.songname:
                header_parts.append(self.songname)
            if self.singer:
                header_parts.append(self.singer)
            header = ' - '.join(header_parts)
            lines.append(f"# {header}")
        
        # 添加歌词内容
        if single_line:
            # 单行输出：用空格连接所有歌词行
            lyric_text = ' '.join(self.lyrics)
            if lines:
                lines.append(lyric_text)
            else:
                lines = [lyric_text]
        else:
            # 多行输出：每行歌词单独一行
            lines.extend(self.lyrics)
        
        return '\n'.join(lines)
    
    def process_file(self, input_path: str, output_path: str, 
                    include_header: bool = True, single_line: bool = False,
                    encoding: str = 'utf-8') -> bool:
        """
        处理单个文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            include_header: 是否包含歌名和歌手信息
            single_line: 是否输出为单行
            encoding: 输出文件编码
        
        Returns:
            是否处理成功
        """
        if not self.parse_file(input_path):
            return False
        
        text = self.to_text(include_header, single_line)
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(output_path, 'w', encoding=encoding) as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"写入文件失败: {e}")
            return False


def batch_process(input_path: str, output_dir: str, 
                 include_header: bool = True, single_line: bool = False,
                 encoding: str = 'utf-8', 
                 progress_callback=None) -> Tuple[int, int]:
    """
    批量处理文件或文件夹
    
    Args:
        input_path: 输入文件或文件夹路径
        output_dir: 输出目录路径
        include_header: 是否包含歌名和歌手信息
        single_line: 是否输出为单行
        encoding: 文件编码
        progress_callback: 进度回调函数 (current, total)
    
    Returns:
        (成功数量, 总数量)
    """
    processor = LyricProcessor()
    files_to_process = []
    
    # 收集要处理的文件
    if os.path.isfile(input_path):
        files_to_process.append(input_path)
    elif os.path.isdir(input_path):
        for root, dirs, files in os.walk(input_path):
            for file in files:
                if file.endswith('.txt') or file.endswith('.karaoke'):
                    files_to_process.append(os.path.join(root, file))
    
    if not files_to_process:
        return (0, 0)
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    success_count = 0
    total_count = len(files_to_process)
    
    for idx, input_file in enumerate(files_to_process, 1):
        # 生成输出文件名 - 保留原文件名，但统一使用 .txt 扩展名
        base_name = os.path.basename(input_file)
        # 移除原扩展名，统一使用 .txt
        name_without_ext = os.path.splitext(base_name)[0]
        output_file = os.path.join(output_dir, f"{name_without_ext}.txt")
        
        if processor.process_file(input_file, output_file, include_header, single_line, encoding):
            success_count += 1
        
        # 调用进度回调
        if progress_callback:
            progress_callback(idx, total_count)
    
    return (success_count, total_count)

