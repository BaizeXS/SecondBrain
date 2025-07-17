"""BibTeX parsing and citation management service."""

import logging
import re
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class BibTeXParser:
    """BibTeX解析器."""

    def __init__(self) -> None:
        self.entry_types = {
            'article', 'book', 'booklet', 'inbook', 'incollection',
            'inproceedings', 'manual', 'mastersthesis', 'misc',
            'phdthesis', 'proceedings', 'techreport', 'unpublished'
        }

    def parse_bibtex(self, bibtex_content: str) -> list[dict[str, Any]]:
        """解析BibTeX内容."""
        entries = []

        # 查找所有BibTeX条目
        pattern = r'@(\w+)\s*\{\s*([^,]+),\s*((?:[^{}]|{[^{}]*})*)\}'
        matches = re.finditer(pattern, bibtex_content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            entry_type = match.group(1).lower()
            bibtex_key = match.group(2).strip()
            entry_content = match.group(3)

            if entry_type in self.entry_types:
                entry = self._parse_entry(entry_type, bibtex_key, entry_content)
                entry['bibtex_raw'] = match.group(0)
                entries.append(entry)

        return entries

    def _parse_entry(self, entry_type: str, bibtex_key: str, content: str) -> dict[str, Any]:
        """解析单个BibTeX条目."""
        entry: dict[str, Any] = {
            'citation_type': entry_type,
            'bibtex_key': bibtex_key,
            'fields': {}
        }

        # 解析字段
        field_pattern = r'(\w+)\s*=\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}'
        field_matches = re.finditer(field_pattern, content)

        for field in field_matches:
            field_name = field.group(1).lower()
            field_value = field.group(2).strip()

            # 清理字段值
            field_value = self._clean_field_value(field_value)
            entry['fields'][field_name] = field_value

        # 提取常用字段
        fields_dict = entry['fields']
        entry['title'] = fields_dict.get('title', '')
        entry['year'] = self._parse_year(fields_dict.get('year', ''))
        entry['authors'] = self._parse_authors(fields_dict.get('author', ''))
        entry['journal'] = fields_dict.get('journal')
        entry['volume'] = fields_dict.get('volume')
        entry['number'] = fields_dict.get('number')
        entry['pages'] = fields_dict.get('pages')
        entry['publisher'] = fields_dict.get('publisher')
        entry['booktitle'] = fields_dict.get('booktitle')
        entry['doi'] = fields_dict.get('doi')
        entry['isbn'] = fields_dict.get('isbn')
        entry['url'] = fields_dict.get('url')
        entry['abstract'] = fields_dict.get('abstract')
        entry['keywords'] = self._parse_keywords(fields_dict.get('keywords', ''))

        return entry

    def _clean_field_value(self, value: str) -> str:
        """清理字段值."""
        # 移除多余的空白
        value = ' '.join(value.split())

        # 移除LaTeX命令（简化版）
        value = re.sub(r'\\[a-zA-Z]+{([^}]*)}', r'\1', value)
        value = re.sub(r'\\[a-zA-Z]+\s*', '', value)

        # 移除大括号
        value = value.replace('{', '').replace('}', '')

        return value.strip()

    def _parse_authors(self, author_string: str) -> list[str]:
        """解析作者列表."""
        if not author_string:
            return []

        # 按 and 分割
        authors = re.split(r'\s+and\s+', author_string)

        # 清理每个作者名字
        cleaned_authors = []
        for author in authors:
            author = author.strip()
            if author:
                # 处理 "Last, First" 格式
                if ',' in author:
                    parts = author.split(',', 1)
                    author = f"{parts[1].strip()} {parts[0].strip()}"
                cleaned_authors.append(author)

        return cleaned_authors

    def _parse_year(self, year_string: str) -> int | None:
        """解析年份."""
        if not year_string:
            return None

        # 提取4位数字
        match = re.search(r'\b(19\d{2}|20\d{2})\b', year_string)
        if match:
            return int(match.group(1))

        return None

    def _parse_keywords(self, keywords_string: str) -> list[str]:
        """解析关键词."""
        if not keywords_string:
            return []

        # 按逗号或分号分割
        keywords = re.split(r'[,;]', keywords_string)

        # 清理并去重
        cleaned_keywords = []
        seen = set()
        for keyword in keywords:
            keyword = keyword.strip()
            if keyword and keyword.lower() not in seen:
                cleaned_keywords.append(keyword)
                seen.add(keyword.lower())

        return cleaned_keywords

    def format_citation(self, citation: dict[str, Any], style: str = "apa") -> str:
        """格式化引用（简化版）."""
        if style == "apa":
            return self._format_apa(citation)
        elif style == "mla":
            return self._format_mla(citation)
        elif style == "chicago":
            return self._format_chicago(citation)
        elif style == "ieee":
            return self._format_ieee(citation)
        else:
            return self._format_apa(citation)  # 默认APA

    def _format_apa(self, citation: dict[str, Any]) -> str:
        """APA格式."""
        authors = citation.get('authors', [])
        year = citation.get('year', 'n.d.')
        title = citation.get('title', 'Untitled')

        # 格式化作者
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} & {authors[1]}"
        else:
            author_str = f"{authors[0]} et al."

        # 基本格式
        result = f"{author_str} ({year}). {title}."

        # 根据类型添加额外信息
        if citation['citation_type'] == 'article':
            journal = citation.get('journal', '')
            volume = citation.get('volume', '')
            pages = citation.get('pages', '')

            if journal:
                result += f" {journal}"
                if volume:
                    result += f", {volume}"
                if pages:
                    result += f", {pages}"
                result += "."

        elif citation['citation_type'] == 'book':
            publisher = citation.get('publisher', '')
            if publisher:
                result += f" {publisher}."

        return result

    def _format_mla(self, citation: dict[str, Any]) -> str:
        """MLA格式（简化版）."""
        authors = citation.get('authors', [])
        title = citation.get('title', 'Untitled')
        year = citation.get('year', 'n.d.')

        # 格式化作者
        if len(authors) == 0:
            author_str = "Unknown"
        elif len(authors) == 1:
            # Last, First格式
            parts = authors[0].split()
            if len(parts) >= 2:
                author_str = f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                author_str = authors[0]
        else:
            # 第一个作者Last, First，其他First Last
            parts = authors[0].split()
            if len(parts) >= 2:
                author_str = f"{parts[-1]}, {' '.join(parts[:-1])}"
            else:
                author_str = authors[0]

            if len(authors) == 2:
                author_str += f", and {authors[1]}"
            else:
                author_str += ", et al."

        # 基本格式
        result = f'{author_str}. "{title}."'

        # 根据类型添加信息
        if citation['citation_type'] == 'article':
            journal = citation.get('journal', '')
            if journal:
                result += f" {journal}"
            result += f" ({year})"

            pages = citation.get('pages', '')
            if pages:
                result += f": {pages}"
            result += "."
        else:
            result += f" {year}."

        return result

    def _format_chicago(self, citation: dict[str, Any]) -> str:
        """Chicago格式（简化版）."""
        # 类似APA但有细微差别
        return self._format_apa(citation)

    def _format_ieee(self, citation: dict[str, Any]) -> str:
        """IEEE格式（简化版）."""
        authors = citation.get('authors', [])
        title = citation.get('title', 'Untitled')
        year = citation.get('year', 'n.d.')

        # 格式化作者（首字母+姓）
        author_parts = []
        for author in authors[:3]:  # 最多3个作者
            parts = author.split()
            if len(parts) >= 2:
                initials = '. '.join([p[0] for p in parts[:-1]]) + '.'
                author_parts.append(f"{initials} {parts[-1]}")
            else:
                author_parts.append(author)

        if len(authors) > 3:
            author_parts.append("et al.")

        author_str = ", ".join(author_parts)

        # 基本格式
        result = f'{author_str}, "{title},"'

        # 根据类型添加信息
        if citation['citation_type'] == 'article':
            journal = citation.get('journal', '')
            volume = citation.get('volume', '')
            pages = citation.get('pages', '')

            if journal:
                result += f" {journal}"
                if volume:
                    result += f", vol. {volume}"
                if pages:
                    result += f", pp. {pages}"
            result += f", {year}."
        else:
            result += f" {year}."

        return result

    def export_bibtex(self, citations: list[dict[str, Any]]) -> str:
        """导出为BibTeX格式."""
        entries = []

        for citation in citations:
            if 'bibtex_raw' in citation and citation['bibtex_raw']:
                entries.append(citation['bibtex_raw'])
            else:
                # 重新构建BibTeX条目
                entry = self._build_bibtex_entry(citation)
                entries.append(entry)

        return '\n\n'.join(entries)

    def _build_bibtex_entry(self, citation: dict[str, Any]) -> str:
        """构建BibTeX条目."""
        entry_type = citation.get('citation_type', 'misc')
        bibtex_key = citation.get('bibtex_key', f"ref{datetime.now().timestamp()}")

        lines = [f"@{entry_type}{{{bibtex_key},"]

        # 添加字段
        if citation.get('title'):
            lines.append(f'  title = {{{citation["title"]}}},')

        if citation.get('authors'):
            author_str = ' and '.join(citation['authors'])
            lines.append(f'  author = {{{author_str}}},')

        if citation.get('year'):
            lines.append(f'  year = {{{citation["year"]}}},')

        # 其他字段
        field_mapping = {
            'journal': 'journal',
            'volume': 'volume',
            'number': 'number',
            'pages': 'pages',
            'publisher': 'publisher',
            'booktitle': 'booktitle',
            'doi': 'doi',
            'isbn': 'isbn',
            'url': 'url',
            'abstract': 'abstract',
        }

        for key, bibtex_field in field_mapping.items():
            if citation.get(key):
                lines.append(f'  {bibtex_field} = {{{citation[key]}}},')

        if citation.get('keywords'):
            keywords_str = ', '.join(citation['keywords'])
            lines.append(f'  keywords = {{{keywords_str}}},')

        # 移除最后一个逗号
        if lines[-1].endswith(','):
            lines[-1] = lines[-1][:-1]

        lines.append('}')

        return '\n'.join(lines)


# 创建全局实例
bibtex_parser = BibTeXParser()
