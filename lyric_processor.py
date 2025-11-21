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
        
        # 新策略：
        # 1. 从左往右解析前两个参数（时间戳，格式简单且不含引号）
        # 2. 剩余部分是 '歌词', '编号'
        # 3. 找到最后一个参数（编号），剩余的就是歌词
        try:
            # 从左往右找前两个"在引号外"的逗号
            # 时间戳格式简单，不会有内嵌引号的问题
            commas_outside_quotes = []
            i = 0
            in_quotes = False
            quote_char = None
            
            while i < len(params_str):
                char = params_str[i]
                
                if char in ["'", '"']:
                    if not in_quotes:
                        # 进入引号
                        in_quotes = True
                        quote_char = char
                    elif char == quote_char:
                        # 可能退出引号，或者是转义的引号
                        if i + 1 < len(params_str) and params_str[i + 1] == quote_char:
                            # 这是转义的引号，跳过下一个字符
                            i += 1
                        else:
                            # 退出引号
                            in_quotes = False
                            quote_char = None
                elif char == ',' and not in_quotes:
                    # 这是一个在引号外的逗号
                    commas_outside_quotes.append(i)
                    # 我们只需要前两个逗号
                    if len(commas_outside_quotes) >= 2:
                        break
                
                i += 1
            
            # 现在我们有了前两个逗号的位置
            # 第一个逗号分隔时间1和时间2
            # 第二个逗号分隔时间2和歌词
            if len(commas_outside_quotes) < 2:
                return self._extract_third_param_fallback(params_str)
            
            # 从第二个逗号之后开始，剩余部分是: '歌词', '编号'
            remaining = params_str[commas_outside_quotes[1] + 1:].strip()
            
            # 现在我们需要分离歌词和编号
            # 从右往左找最后一个参数（编号）
            # 编号的格式是 '数字'，很简单
            
            # 找到最后一个引号（编号的结束）
            last_quote_pos = max(remaining.rfind("'"), remaining.rfind('"'))
            if last_quote_pos == -1:
                return self._extract_third_param_fallback(params_str)
            
            quote_char = remaining[last_quote_pos]
            
            # 找到与之配对的开始引号
            # 从 last_quote_pos-1 往左找
            number_start_quote = remaining.rfind(quote_char, 0, last_quote_pos)
            if number_start_quote == -1:
                return self._extract_third_param_fallback(params_str)
            
            # 现在 number_start_quote 到 last_quote_pos 之间是编号参数
            # 找到编号参数之前的逗号
            comma_before_number = remaining.rfind(',', 0, number_start_quote)
            if comma_before_number == -1:
                return self._extract_third_param_fallback(params_str)
            
            # 提取歌词部分（从开始到这个逗号）
            lyric_param = remaining[:comma_before_number].strip()
            
            # 去除外层引号
            if len(lyric_param) >= 2:
                if (lyric_param.startswith("'") and lyric_param.endswith("'")) or \
                   (lyric_param.startswith('"') and lyric_param.endswith('"')):
                    lyric_text = lyric_param[1:-1]
                    # 处理转义的引号
                    if lyric_param[0] == "'":
                        lyric_text = lyric_text.replace("''", "'")
                    else:
                        lyric_text = lyric_text.replace('""', '"')
                    return lyric_text
            
            return lyric_param
            
        except Exception:
            # 如果解析失败，使用备用方法
            return self._extract_third_param_fallback(params_str)
    
    def _extract_third_param_fallback(self, params_str: str) -> str:
        """
        备用方法：手动解析参数（当正则表达式失败时使用）
        尝试找到第三个逗号分隔的参数
        
        这个方法使用状态机来解析参数，能够正确处理：
        1. 引号内的逗号（不作为分隔符）
        2. 转义的引号（两个连续的相同引号，如 '' 或 ""）
        3. 混合的引号类型
        """
        # 简单方法：按逗号分割，但需要智能处理引号内的逗号
        params = []
        i = 0
        current_param = ""
        in_quotes = False
        quote_char = None
        
        while i < len(params_str):
            char = params_str[i]
            
            if char in ['"', "'"]:
                if not in_quotes:
                    # 进入引号
                    in_quotes = True
                    quote_char = char
                    current_param += char
                elif char == quote_char:
                    # 可能退出引号，或者是转义的引号
                    # 检查下一个字符是否是相同的引号（转义）
                    if i + 1 < len(params_str) and params_str[i + 1] == quote_char:
                        # 这是转义的引号，保留两个引号
                        current_param += char + char
                        i += 1  # 跳过下一个引号
                    else:
                        # 这是引号的结束
                        current_param += char
                        in_quotes = False
                        quote_char = None
                else:
                    # 在引号内，但是遇到了不同类型的引号，直接添加
                    current_param += char
            elif char == ',' and not in_quotes:
                # 这是参数分隔符
                params.append(current_param.strip())
                current_param = ""
            else:
                # 普通字符
                current_param += char
            
            i += 1
        
        # 添加最后一个参数
        if current_param.strip():
            params.append(current_param.strip())
        
        # 提取第三个参数
        if len(params) >= 3:
            third = params[2].strip()
            # 去除外层引号
            if (third.startswith("'") and third.endswith("'")) or \
               (third.startswith('"') and third.endswith('"')):
                third = third[1:-1]
                # 处理转义的引号：两个连续的相同引号变成一个引号
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

