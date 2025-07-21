# SecondBrain 测试文档

## 概述
这是一个Markdown格式的测试文档，用于API测试。

## 主要章节

### 1. 介绍
SecondBrain是一个知识管理系统，支持文档管理、笔记创建和AI分析。

### 2. 功能特点
- **文档管理**：支持多种格式的文档上传和管理
- **智能搜索**：基于向量的语义搜索
- **AI分析**：使用大语言模型进行内容分析

### 3. 测试场景
1. 文档上传测试
2. 内容提取测试
3. 搜索功能测试
4. 标注功能测试

## 代码示例
```python
def test_upload():
    """测试文档上传功能"""
    response = api.upload_document("test.txt")
    assert response.status_code == 201
```

## 总结
这个文档包含了各种格式的内容，适合用于全面的API测试。