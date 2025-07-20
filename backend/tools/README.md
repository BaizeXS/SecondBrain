# SecondBrain 开发工具集

为 SecondBrain 项目提供完整的测试、数据管理和调试工具。

## 📁 工具列表

### 1. **api_test_suite.py** - API 测试套件

完整的 API 端点测试工具，覆盖所有 100+个端点。

```bash
uv run python tools/api_test_suite.py
```

**功能特点：**

- ✅ 100%端点覆盖（106 个端点）
- ✅ 模块化测试架构
- ✅ 详细测试报告
- ✅ 自动数据清理
- ✅ JSON 格式报告输出

### 2. **integration_test.py** - 集成测试

核心业务流程的端到端测试。

```bash
uv run python tools/integration_test.py
```

**功能特点：**

- 🔄 真实用户场景模拟
- 🔄 跨模块功能验证
- 🔄 业务流程完整性检查
- 🔄 快速问题诊断

### 3. **demo_data_creator.py** - 演示数据创建器

自动创建演示数据，展示系统完整功能。

```bash
uv run python tools/demo_data_creator.py
```

**功能特点：**

- 📊 创建演示用户账号
- 📊 生成知识空间和文档
- 📊 创建笔记和对话示例
- 📊 保存创建报告

### 4. **database_cleaner.py** - 数据库清理工具

清理测试数据或重置数据库状态。

```bash
# 清理测试数据（保留演示账号）
uv run python tools/database_cleaner.py

# 重置演示数据
uv run python tools/database_cleaner.py --reset-demo

# 查看数据库统计
uv run python tools/database_cleaner.py --stats

# 完全重置（危险操作）
uv run python tools/database_cleaner.py --full-reset
```

**功能特点：**

- 🧹 智能清理测试数据
- 🧹 保留演示账号选项
- 🧹 数据库统计信息
- 🧹 安全的级联删除

### 5. **openrouter_test.py** - OpenRouter 测试

验证 AI 模型配置和连接状态。

```bash
uv run python tools/openrouter_test.py
```

**功能特点：**

- 🤖 API 连接验证
- 🤖 模型可用性检查
- 🤖 免费额度查询
- 🤖 模型路由测试

### 6. **web_test_server.py** + **test_web_interface.html** - Web 测试界面

提供交互式的 API 测试界面（包含基础版和增强版）。

```bash
# 启动基础版界面
uv run python tools/web_test_server.py

# 启动增强版界面
uv run python tools/web_test_server.py --enhanced
# 或
uv run python tools/web_test_server.py -e

# 访问 http://localhost:8080
```

**基础版功能：**

- 🌐 可视化 API 测试
- 🌐 实时响应查看
- 🌐 支持核心端点
- 🌐 适合快速调试

**增强版新增功能：**

- 📊 实时性能监控仪表板
- 📈 响应时间趋势图表
- 🔄 批量测试功能
- 📜 请求历史记录
- 🛠️ 自定义请求构建器
- 💾 测试结果导出
- 🎯 快速测试场景
- 📱 响应式设计

### 7. **performance_test_suite.py** - 性能测试套件

综合性能测试工具，测试 API 的响应时间、并发能力和稳定性。

```bash
uv run python tools/performance_test_suite.py
```

**测试内容：**

- ⚡ 端点性能测试（响应时间统计）
- 🔄 并发请求测试
- 🏋️ 负载测试（持续 QPS）
- 🔥 压力测试（递增负载）
- 🔧 复杂工作流程测试

**输出指标：**

- 平均响应时间、P95、P99 延迟
- 吞吐量（QPS）
- 成功率和错误率
- 详细的 JSON 报告

## 🚀 快速开始

### 1. 环境准备

**安装 UV 包管理器：**

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**设置项目环境：**

```bash
# 进入后端目录
cd backend

# 安装依赖（自动创建虚拟环境）
uv sync

# 确保Docker服务运行
docker-compose up -d

# 检查服务状态
docker-compose ps
```

### 2. 基础测试流程

```bash
# 1. 创建演示数据
uv run python tools/demo_data_creator.py

# 2. 运行集成测试
uv run python tools/integration_test.py

# 3. 完整API测试
uv run python tools/api_test_suite.py

# 4. 清理测试数据
uv run python tools/database_cleaner.py
```

### 3. 开发调试流程

```bash
# 1. 启动Web测试界面
uv run python tools/web_test_server.py

# 2. 手动测试特定接口
# 访问 http://localhost:8080

# 3. 查看数据库状态
uv run python tools/database_cleaner.py --stats
```

## 📊 测试覆盖统计

| 模块     | 端点数  | 测试覆盖  | 备注                    |
| -------- | ------- | --------- | ----------------------- |
| 认证     | 8       | 100%      | ✅                      |
| 用户     | 5       | 100%      | ✅                      |
| 空间     | 6       | 100%      | ✅                      |
| 文档     | 14      | 92.9%     | 1 个 URL 分析功能未实现 |
| 笔记     | 20      | 100%      | ✅                      |
| 聊天     | 15      | 100%      | ✅                      |
| 代理     | 5       | 80%       | 自定义代理创建未实现    |
| 引用     | 7       | 100%      | ✅                      |
| 标注     | 14      | 100%      | ✅                      |
| 导出     | 4       | 50%       | 部分导出格式未实现      |
| Ollama   | 6       | 100%      | ✅                      |
| **总计** | **106** | **95.3%** | 5 个端点失败            |

## 🎯 使用场景

### 日常开发

```bash
# 快速验证
uv run python tools/integration_test.py
```

### 部署前检查

```bash
# 完整测试
uv run python tools/api_test_suite.py

# 清理数据
uv run python tools/database_cleaner.py
```

### 演示准备

```bash
# 创建演示数据
uv run python tools/demo_data_creator.py

# 验证功能
uv run python tools/integration_test.py
```

### 问题诊断

```bash
# 查看数据库状态
uv run python tools/database_cleaner.py --stats

# Web界面调试
uv run python tools/web_test_server.py
```

## 💡 UV 使用技巧

### 常用命令

```bash
# 查看已安装包
uv pip list

# 添加新依赖
uv add package-name

# 添加开发依赖
uv add --group dev package-name

# 更新所有依赖
uv sync --upgrade

# 运行测试
uv run pytest

# 激活虚拟环境（如需要）
source .venv/bin/activate  # Unix/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 环境管理

```bash
# 重新创建环境
uv sync --reinstall

# 清理未使用的包
uv pip list --outdated

# 导出需求文件（兼容性）
uv pip freeze > requirements.txt
```

## ⚠️ 注意事项

1. **环境要求**

   - UV 包管理器 (推荐最新版本)
   - Docker 和 Docker Compose
   - Python 3.12+
   - 端口 8000 和 8080 需要可用

2. **首次使用**

   - 运行 `uv sync` 会自动创建虚拟环境并安装依赖
   - 确保配置.env 文件
   - 项目依赖会自动从 `uv.lock` 文件同步

3. **数据安全**

   - database_cleaner.py 会删除数据，请谨慎使用
   - --full-reset 会清空整个数据库
   - 建议先用--stats 查看状态

4. **测试账号**

   - 演示账号：demo_user / Demo123456!
   - 测试账号：自动生成带时间戳

5. **API 限制**
   - 某些功能需要 Premium 权限
   - 空间数量有限制
   - 部分导出格式未实现

## 📝 测试报告

所有测试工具都会生成详细报告：

- `api_test_report_*.json` - API 测试详细报告
- `demo_data_summary.json` - 演示数据创建报告
- 控制台实时输出测试进度

## 🔧 故障排除

### UV 相关问题

```bash
# 检查 UV 版本
uv --version

# 重新同步依赖
uv sync --reinstall

# 清除缓存
uv cache clean
```

### 连接失败

```bash
docker-compose ps
docker-compose logs -f backend
```

### 权限错误

```bash
cat .env | grep API_KEY
```

### 数据库问题

```bash
docker-compose exec backend alembic upgrade head
```

### 端口占用

```bash
lsof -i :8000
lsof -i :8080
```

## 🚀 性能优化建议

- 使用 `uv run` 命令可以避免每次手动激活虚拟环境
- UV 的依赖解析比 pip 更快，特别适合大型项目
- 定期运行 `uv sync` 保持依赖同步
- 使用 `uv.lock` 确保团队环境一致性
