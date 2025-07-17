"""Unit tests for BibTeX Service."""

import pytest

from app.services.bibtex_service import BibTeXParser


@pytest.fixture
def bibtex_parser():
    """创建BibTeX解析器实例."""
    return BibTeXParser()


@pytest.fixture
def sample_bibtex():
    """示例BibTeX内容."""
    return """
@article{smith2020example,
  title = {An Example Article Title},
  author = {Smith, John and Doe, Jane},
  journal = {Journal of Examples},
  year = {2020},
  volume = {10},
  number = {3},
  pages = {123-456},
  doi = {10.1234/example.2020},
  abstract = {This is an example abstract with some text.},
  keywords = {example, testing, bibtex}
}

@book{johnson2019book,
  title = {The Great Book of Testing},
  author = {Johnson, Robert},
  publisher = {Test Publishers Inc.},
  year = {2019},
  isbn = {978-0-123456-78-9},
  url = {https://example.com/book}
}

@inproceedings{lee2021conference,
  title = {Conference Paper Example},
  author = {Lee, Alice and Chen, Bob and Wang, Charlie},
  booktitle = {Proceedings of the Test Conference},
  year = {2021},
  pages = {789-801},
  abstract = {A conference paper abstract.}
}
"""


@pytest.fixture
def parsed_article():
    """解析后的文章数据."""
    return {
        'citation_type': 'article',
        'bibtex_key': 'smith2020example',
        'title': 'An Example Article Title',
        'year': 2020,
        'authors': ['John Smith', 'Jane Doe'],
        'journal': 'Journal of Examples',
        'volume': '10',
        'number': '3',
        'pages': '123-456',
        'doi': '10.1234/example.2020',
        'abstract': 'This is an example abstract with some text.',
        'keywords': ['example', 'testing', 'bibtex']
    }


class TestParseBibTeX:
    """测试BibTeX解析功能."""

    def test_parse_bibtex_multiple_entries(self, bibtex_parser, sample_bibtex):
        """测试解析多个BibTeX条目."""
        entries = bibtex_parser.parse_bibtex(sample_bibtex)

        assert len(entries) == 3
        assert entries[0]['citation_type'] == 'article'
        assert entries[1]['citation_type'] == 'book'
        assert entries[2]['citation_type'] == 'inproceedings'

    def test_parse_bibtex_article(self, bibtex_parser, sample_bibtex):
        """测试解析文章条目."""
        entries = bibtex_parser.parse_bibtex(sample_bibtex)
        article = entries[0]

        assert article['bibtex_key'] == 'smith2020example'
        assert article['title'] == 'An Example Article Title'
        assert article['year'] == 2020
        assert article['authors'] == ['John Smith', 'Jane Doe']
        assert article['journal'] == 'Journal of Examples'
        assert article['volume'] == '10'
        assert article['number'] == '3'
        assert article['pages'] == '123-456'
        assert article['doi'] == '10.1234/example.2020'
        assert article['keywords'] == ['example', 'testing', 'bibtex']

    def test_parse_bibtex_book(self, bibtex_parser, sample_bibtex):
        """测试解析书籍条目."""
        entries = bibtex_parser.parse_bibtex(sample_bibtex)
        book = entries[1]

        assert book['bibtex_key'] == 'johnson2019book'
        assert book['title'] == 'The Great Book of Testing'
        assert book['authors'] == ['Robert Johnson']
        assert book['publisher'] == 'Test Publishers Inc.'
        assert book['year'] == 2019
        assert book['isbn'] == '978-0-123456-78-9'
        assert book['url'] == 'https://example.com/book'

    def test_parse_bibtex_conference(self, bibtex_parser, sample_bibtex):
        """测试解析会议论文条目."""
        entries = bibtex_parser.parse_bibtex(sample_bibtex)
        conf = entries[2]

        assert conf['bibtex_key'] == 'lee2021conference'
        assert conf['title'] == 'Conference Paper Example'
        assert conf['authors'] == ['Alice Lee', 'Bob Chen', 'Charlie Wang']
        assert conf['booktitle'] == 'Proceedings of the Test Conference'
        assert conf['year'] == 2021
        assert conf['pages'] == '789-801'

    def test_parse_bibtex_empty(self, bibtex_parser):
        """测试解析空内容."""
        entries = bibtex_parser.parse_bibtex("")
        assert entries == []

    def test_parse_bibtex_invalid_entry(self, bibtex_parser):
        """测试解析无效条目."""
        bibtex = "@invalidtype{key, title={Test}}"
        entries = bibtex_parser.parse_bibtex(bibtex)
        assert entries == []  # 无效类型应被忽略

    def test_parse_bibtex_raw_preserved(self, bibtex_parser):
        """测试保留原始BibTeX内容."""
        bibtex = "@article{test, title={Test Article}}"
        entries = bibtex_parser.parse_bibtex(bibtex)

        assert len(entries) == 1
        assert 'bibtex_raw' in entries[0]
        assert entries[0]['bibtex_raw'] == bibtex


class TestParseAuthors:
    """测试作者解析功能."""

    def test_parse_authors_single(self, bibtex_parser):
        """测试解析单个作者."""
        authors = bibtex_parser._parse_authors("John Smith")
        assert authors == ["John Smith"]

    def test_parse_authors_multiple(self, bibtex_parser):
        """测试解析多个作者."""
        authors = bibtex_parser._parse_authors("John Smith and Jane Doe and Bob Johnson")
        assert authors == ["John Smith", "Jane Doe", "Bob Johnson"]

    def test_parse_authors_last_first_format(self, bibtex_parser):
        """测试解析Last, First格式."""
        authors = bibtex_parser._parse_authors("Smith, John and Doe, Jane")
        assert authors == ["John Smith", "Jane Doe"]

    def test_parse_authors_mixed_format(self, bibtex_parser):
        """测试解析混合格式."""
        authors = bibtex_parser._parse_authors("Smith, John and Jane Doe")
        assert authors == ["John Smith", "Jane Doe"]

    def test_parse_authors_empty(self, bibtex_parser):
        """测试解析空作者."""
        assert bibtex_parser._parse_authors("") == []
        assert bibtex_parser._parse_authors(None) == []

    def test_parse_authors_whitespace(self, bibtex_parser):
        """测试处理多余空白."""
        authors = bibtex_parser._parse_authors("  John   Smith   and   Jane   Doe  ")
        # 注意：当前实现不会规范化作者名内部的空白
        assert authors == ["John   Smith", "Jane   Doe"]


class TestParseYear:
    """测试年份解析功能."""

    def test_parse_year_valid(self, bibtex_parser):
        """测试解析有效年份."""
        assert bibtex_parser._parse_year("2020") == 2020
        assert bibtex_parser._parse_year("1999") == 1999
        assert bibtex_parser._parse_year("2023") == 2023

    def test_parse_year_with_text(self, bibtex_parser):
        """测试从文本中提取年份."""
        assert bibtex_parser._parse_year("Published in 2020") == 2020
        assert bibtex_parser._parse_year("Year: 1999") == 1999

    def test_parse_year_invalid(self, bibtex_parser):
        """测试解析无效年份."""
        assert bibtex_parser._parse_year("") is None
        assert bibtex_parser._parse_year("invalid") is None
        assert bibtex_parser._parse_year("99") is None  # 不是4位数
        assert bibtex_parser._parse_year("3020") is None  # 未来年份


class TestParseKeywords:
    """测试关键词解析功能."""

    def test_parse_keywords_comma_separated(self, bibtex_parser):
        """测试逗号分隔的关键词."""
        keywords = bibtex_parser._parse_keywords("machine learning, deep learning, AI")
        assert keywords == ["machine learning", "deep learning", "AI"]

    def test_parse_keywords_semicolon_separated(self, bibtex_parser):
        """测试分号分隔的关键词."""
        keywords = bibtex_parser._parse_keywords("python; java; c++")
        assert keywords == ["python", "java", "c++"]

    def test_parse_keywords_mixed_separators(self, bibtex_parser):
        """测试混合分隔符."""
        keywords = bibtex_parser._parse_keywords("test1, test2; test3, test4")
        assert keywords == ["test1", "test2", "test3", "test4"]

    def test_parse_keywords_duplicates(self, bibtex_parser):
        """测试去重功能."""
        keywords = bibtex_parser._parse_keywords("test, Test, TEST, test")
        assert keywords == ["test"]

    def test_parse_keywords_empty(self, bibtex_parser):
        """测试空关键词."""
        assert bibtex_parser._parse_keywords("") == []
        assert bibtex_parser._parse_keywords(None) == []

    def test_parse_keywords_whitespace(self, bibtex_parser):
        """测试处理空白."""
        keywords = bibtex_parser._parse_keywords("  test1  ,   test2  ;  test3  ")
        assert keywords == ["test1", "test2", "test3"]


class TestCleanFieldValue:
    """测试字段值清理功能."""

    def test_clean_field_value_whitespace(self, bibtex_parser):
        """测试清理空白."""
        assert bibtex_parser._clean_field_value("  test  value  ") == "test value"
        assert bibtex_parser._clean_field_value("test\n\nvalue") == "test value"

    def test_clean_field_value_latex_commands(self, bibtex_parser):
        """测试移除LaTeX命令."""
        assert bibtex_parser._clean_field_value(r"\textit{italic}") == "italic"
        assert bibtex_parser._clean_field_value(r"\textbf{bold}") == "bold"
        assert bibtex_parser._clean_field_value(r"\emph{emphasis}") == "emphasis"

    def test_clean_field_value_braces(self, bibtex_parser):
        """测试移除大括号."""
        assert bibtex_parser._clean_field_value("{test}") == "test"
        assert bibtex_parser._clean_field_value("{{nested}}") == "nested"

    def test_clean_field_value_complex(self, bibtex_parser):
        """测试复杂清理."""
        value = r"  \textit{Complex}  {test}  with \textbf{multiple} parts  "
        expected = "Complex test with multiple parts"
        assert bibtex_parser._clean_field_value(value) == expected


class TestFormatCitation:
    """测试引用格式化功能."""

    def test_format_apa_article(self, bibtex_parser, parsed_article):
        """测试APA格式文章引用."""
        result = bibtex_parser.format_citation(parsed_article, "apa")
        assert "John Smith & Jane Doe (2020)" in result
        assert "An Example Article Title" in result
        assert "Journal of Examples" in result

    def test_format_apa_single_author(self, bibtex_parser):
        """测试APA格式单作者."""
        citation = {
            'citation_type': 'article',
            'authors': ['John Smith'],
            'year': 2020,
            'title': 'Test Title'
        }
        result = bibtex_parser.format_citation(citation, "apa")
        assert "John Smith (2020)" in result

    def test_format_apa_multiple_authors(self, bibtex_parser):
        """测试APA格式多作者."""
        citation = {
            'citation_type': 'article',
            'authors': ['A Author', 'B Author', 'C Author', 'D Author'],
            'year': 2020,
            'title': 'Test Title'
        }
        result = bibtex_parser.format_citation(citation, "apa")
        assert "A Author et al. (2020)" in result

    def test_format_apa_book(self, bibtex_parser):
        """测试APA格式书籍引用."""
        citation = {
            'citation_type': 'book',
            'authors': ['John Smith'],
            'year': 2020,
            'title': 'Test Book',
            'publisher': 'Test Publisher'
        }
        result = bibtex_parser.format_citation(citation, "apa")
        assert "Test Publisher" in result

    def test_format_mla_article(self, bibtex_parser):
        """测试MLA格式引用."""
        citation = {
            'citation_type': 'article',
            'authors': ['John Smith'],
            'year': 2020,
            'title': 'Test Article',
            'journal': 'Test Journal'
        }
        result = bibtex_parser.format_citation(citation, "mla")
        assert '"Test Article."' in result
        assert "Test Journal" in result
        assert "(2020)" in result

    def test_format_ieee_article(self, bibtex_parser):
        """测试IEEE格式引用."""
        citation = {
            'citation_type': 'article',
            'authors': ['John Smith', 'Jane Doe'],
            'year': 2020,
            'title': 'Test Article',
            'journal': 'Test Journal',
            'volume': '10',
            'pages': '123-456'
        }
        result = bibtex_parser.format_citation(citation, "ieee")
        assert '"Test Article,"' in result
        assert "vol. 10" in result
        assert "pp. 123-456" in result

    def test_format_default_style(self, bibtex_parser, parsed_article):
        """测试默认格式（应该是APA）."""
        result = bibtex_parser.format_citation(parsed_article, "unknown")
        apa_result = bibtex_parser.format_citation(parsed_article, "apa")
        assert result == apa_result


class TestExportBibTeX:
    """测试导出BibTeX功能."""

    def test_export_bibtex_with_raw(self, bibtex_parser):
        """测试导出带原始内容的引用."""
        citations = [{
            'bibtex_raw': '@article{test, title={Test}}'
        }]
        result = bibtex_parser.export_bibtex(citations)
        assert result == '@article{test, title={Test}}'

    def test_export_bibtex_rebuild(self, bibtex_parser):
        """测试重建BibTeX条目."""
        citations = [{
            'citation_type': 'article',
            'bibtex_key': 'test2020',
            'title': 'Test Article',
            'authors': ['John Smith', 'Jane Doe'],
            'year': 2020,
            'journal': 'Test Journal',
            'volume': '10',
            'pages': '123-456',
            'doi': '10.1234/test',
            'keywords': ['test', 'example']
        }]

        result = bibtex_parser.export_bibtex(citations)

        assert '@article{test2020,' in result
        assert 'title = {Test Article}' in result
        assert 'author = {John Smith and Jane Doe}' in result
        assert 'year = {2020}' in result
        assert 'journal = {Test Journal}' in result
        assert 'volume = {10}' in result
        assert 'pages = {123-456}' in result
        assert 'doi = {10.1234/test}' in result
        assert 'keywords = {test, example}' in result

    def test_export_bibtex_multiple(self, bibtex_parser):
        """测试导出多个引用."""
        citations = [
            {'bibtex_raw': '@article{test1, title={Test1}}'},
            {'bibtex_raw': '@book{test2, title={Test2}}'}
        ]
        result = bibtex_parser.export_bibtex(citations)

        assert '@article{test1, title={Test1}}' in result
        assert '@book{test2, title={Test2}}' in result
        assert '\n\n' in result  # 条目之间应有空行

    def test_export_bibtex_empty(self, bibtex_parser):
        """测试导出空列表."""
        result = bibtex_parser.export_bibtex([])
        assert result == ''

    def test_export_bibtex_minimal(self, bibtex_parser):
        """测试导出最小条目."""
        citations = [{
            'citation_type': 'misc',
            'title': 'Minimal Entry'
        }]

        result = bibtex_parser.export_bibtex(citations)

        assert '@misc{' in result
        assert 'title = {Minimal Entry}' in result


class TestBuildBibTeXEntry:
    """测试构建BibTeX条目功能."""

    def test_build_bibtex_entry_complete(self, bibtex_parser):
        """测试构建完整条目."""
        citation = {
            'citation_type': 'article',
            'bibtex_key': 'smith2020',
            'title': 'Complete Article',
            'authors': ['John Smith'],
            'year': 2020,
            'journal': 'Test Journal',
            'abstract': 'Test abstract'
        }

        result = bibtex_parser._build_bibtex_entry(citation)

        assert '@article{smith2020,' in result
        assert 'title = {Complete Article}' in result
        assert 'author = {John Smith}' in result
        assert 'year = {2020}' in result
        assert 'journal = {Test Journal}' in result
        assert 'abstract = {Test abstract}' in result
        assert result.endswith('}')

    def test_build_bibtex_entry_no_key(self, bibtex_parser):
        """测试没有key时自动生成."""
        citation = {
            'citation_type': 'misc',
            'title': 'No Key Entry'
        }

        result = bibtex_parser._build_bibtex_entry(citation)

        assert '@misc{ref' in result  # 应该生成ref开头的key
        assert 'title = {No Key Entry}' in result

    def test_build_bibtex_entry_optional_fields(self, bibtex_parser):
        """测试可选字段."""
        citation = {
            'citation_type': 'book',
            'bibtex_key': 'book2020',
            'title': 'Test Book',
            'isbn': '123-456',
            'url': 'https://example.com'
        }

        result = bibtex_parser._build_bibtex_entry(citation)

        assert 'isbn = {123-456}' in result
        assert 'url = {https://example.com}' in result


class TestEntryTypes:
    """测试条目类型识别."""

    def test_valid_entry_types(self, bibtex_parser):
        """测试有效的条目类型."""
        valid_types = [
            'article', 'book', 'booklet', 'inbook', 'incollection',
            'inproceedings', 'manual', 'mastersthesis', 'misc',
            'phdthesis', 'proceedings', 'techreport', 'unpublished'
        ]

        for entry_type in valid_types:
            assert entry_type in bibtex_parser.entry_types

    def test_parse_case_insensitive(self, bibtex_parser):
        """测试大小写不敏感解析."""
        bibtex = "@ARTICLE{test, title={Test}}"
        entries = bibtex_parser.parse_bibtex(bibtex)

        assert len(entries) == 1
        assert entries[0]['citation_type'] == 'article'  # 应转换为小写
