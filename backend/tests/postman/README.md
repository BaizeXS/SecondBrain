# SecondBrain API 测试套件

本目录包含SecondBrain后端API的完整测试套件，包括Postman测试集合和Python自动化测试脚本。

## 📁 目录结构

```
postman/
├── comprehensive_api_test.py    # 综合API测试脚本（推荐使用）
├── run_tests.sh                # Newman测试运行脚本
├── API_COVERAGE.md             # API覆盖率详细报告
├── API_COVERAGE_REPORT.json    # API覆盖率JSON数据
├── *.postman_collection.json   # Postman测试集合
├── *.postman_environment.json  # 环境配置文件
└── test_data/                  # 测试数据文件
```

## 🚀 快速开始

### 1. 使用Python综合测试（推荐）

```bash
# 运行所有API测试
python comprehensive_api_test.py

# 查看测试覆盖率
cat API_COVERAGE.md
```

### 2. 使用Newman运行Postman测试

```bash
# 安装Newman
npm install -g newman

# 运行所有Postman测试
./run_tests.sh

# 测试特定环境
./run_tests.sh local   # 测试本地环境
./run_tests.sh server  # 测试服务器环境
```

## 📊 测试覆盖率

当前测试覆盖了**83.2%**的API端点（89/107个）：

| 模块 | 覆盖率 | 已测试/总数 |
|------|--------|-------------|
| 健康检查 | 100% | 2/2 |
| 认证 | 75% | 6/8 |
| 用户管理 | 80% | 4/5 |
| AI聊天 | 66.7% | 10/15 |
| AI代理 | 60% | 3/5 |
| 空间管理 | 80% | 4/5 |
| 文档管理 | 61.5% | 8/13 |
| 笔记管理 | 68.4% | 13/19 |
| 标注功能 | 50% | 6/12 |
| 引用管理 | 66.7% | 6/9 |
| 导出功能 | 50% | 2/4 |
| Ollama | 50% | 3/6 |

详细覆盖情况请查看 [API_COVERAGE.md](./API_COVERAGE.md)

## 🧪 测试功能

### comprehensive_api_test.py 特性

1. **完整的API覆盖**
   - 测试107个API端点中的89个
   - 涵盖所有核心功能模块
   - 智能跳过破坏性操作

2. **AI功能测试**
   - 多模型测试（OpenRouter、GPT-4、Claude等）
   - 流式响应测试
   - 附件对话测试
   - 文档基础对话（PDF对话）

3. **自动化特性**
   - 自动创建测试数据
   - 自动清理测试资源
   - 生成覆盖率报告

4. **错误处理**
   - 支持多个期望状态码
   - 详细的错误信息输出
   - 优雅的失败处理

## ⚙️ 配置

### 环境变量

测试脚本使用以下默认配置：

```python
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "test2@example.com"
PASSWORD = "Test1234!"
```

### 测试账号

请确保存在测试账号：
- 邮箱：test2@example.com
- 密码：Test1234!

如果不存在，脚本会尝试自动注册。

## 📝 Postman测试集合

| 集合文件 | 描述 | 测试数量 |
|---------|------|----------|
| 00_Quick_Test | 快速测试核心功能 | 18个 |
| 01_Auth_Basic | 认证和用户管理 | 14个 |
| 02_Core_Features | 核心功能（空间、笔记、文档） | 46个 |
| 03_AI_Features | AI对话和智能功能 | 49个 |
| 04_Advanced_Features | 高级功能（标注、引用、导出） | 38个 |
| 05_E2E_Complete_Flow | 端到端完整流程 | 11个 |

## 🔧 故障排除

### 常见问题

1. **认证失败**
   - 检查测试账号是否存在
   - 确认密码正确
   - 检查后端服务是否运行

2. **AI测试失败**
   - 检查AI服务API密钥配置
   - 某些模型可能有速率限制
   - 建议使用免费模型进行测试

3. **Ollama测试跳过**
   - 确保Ollama服务正在运行
   - 检查Ollama连接配置

### 调试模式

```bash
# 查看详细输出
python comprehensive_api_test.py -v

# 只运行特定模块的测试
# （需要修改脚本或创建自定义版本）
```

## 🤝 贡献

欢迎贡献更多测试用例！请确保：

1. 新测试遵循现有的代码风格
2. 更新API_COVERAGE.md文档
3. 测试通过后再提交PR

## 📄 许可

本测试套件是SecondBrain项目的一部分，遵循项目的许可协议。