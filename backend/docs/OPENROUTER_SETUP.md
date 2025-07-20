# OpenRouter AI 服务配置指南

## 什么是 OpenRouter？

OpenRouter 是一个统一的 AI 模型网关，允许你通过单一 API 访问多个 AI 提供商的模型，包括：
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- Meta (Llama)
- 以及许多其他开源模型

## 优势

1. **单一 API Key**：只需一个 API Key 即可访问所有模型
2. **自动路由**：使用 `openrouter/auto` 自动选择最佳模型
3. **免费模型**：提供多个免费模型供测试和轻度使用
4. **成本优化**：自动选择性价比最高的模型
5. **无需多个订阅**：避免为每个 AI 提供商单独付费

## 快速设置

### 1. 获取 OpenRouter API Key

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册账号（支持 Google 登录）
3. 进入 [API Keys](https://openrouter.ai/settings/api-keys) 页面
4. 点击 "Create Key" 创建新的 API Key
5. 复制生成的 Key

### 2. 配置后端

在 `.env` 文件中添加：

```env
# OpenRouter API 配置
OPENROUTER_API_KEY=sk-or-v1-你的密钥
OPENROUTER_SITE_URL=http://localhost:8000  # 可选
OPENROUTER_APP_NAME=SecondBrain  # 可选
```

### 3. 测试配置

运行测试脚本验证配置：

```bash
# 确保设置了环境变量
export OPENROUTER_API_KEY=sk-or-v1-你的密钥

# 运行测试
uv run python test_openrouter.py
```

## 支持的模型

### 🆓 免费模型（推荐用于测试）

| 模型 ID | 描述 | 适用场景 |
|---------|------|----------|
| `qwen/qwen3-235b-a22b:free` | 通义千问 235B | 高级推理、长文本 |
| `qwen/qwen3-30b-a3b:free` | 通义千问 30B | 平衡性能与速度 |
| `qwen/qwen3-32b:free` | 通义千问 32B | 中文对话 |
| `deepseek/deepseek-r1-0528:free` | DeepSeek R1 | 推理、分析 |
| `deepseek/deepseek-r1-0528-qwen3-8b:free` | DeepSeek R1 Qwen | 快速推理 |
| `deepseek/deepseek-chat-v3-0324:free` | DeepSeek Chat | 代码、数学 |
| `meta-llama/llama-4-maverick:free` | Llama 4 Maverick | 创意写作 |
| `meta-llama/llama-4-scout:free` | Llama 4 Scout | 通用对话、代码 |
| `moonshotai/kimi-k2:free` | Moonshot Kimi | 长文本处理 |

### 💎 付费模型（更强大的能力）

| 模型 ID | 描述 | 费用估算 |
|---------|------|----------|
| `openai/gpt-4.1` | 最新 GPT-4 | $0.01/1K tokens |
| `openai/gpt-4.1-mini` | GPT-4 Mini | $0.004/1K tokens |
| `openai/o4-mini-high` | O4 Mini 高性能 | 查看官网定价 |
| `openai/o1-pro` | O1 Pro 专业版 | 查看官网定价 |
| `anthropic/claude-opus-4` | Claude Opus 4 | $0.015/1K tokens |
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 | $0.008/1K tokens |
| `anthropic/claude-3.7-sonnet:beta` | Claude 3.7 Sonnet | $0.003/1K tokens |
| `anthropic/claude-3.5-haiku:beta` | Claude 3.5 Haiku | $0.001/1K tokens |
| `google/gemini-2.5-pro` | Gemini 2.5 Pro | $0.002/1K tokens |
| `google/gemini-2.5-flash` | Gemini 2.5 Flash | $0.0005/1K tokens |
| `x-ai/grok-4` | xAI Grok 4 | 查看官网定价 |
| `openrouter/auto` | 自动选择最佳模型 | 根据实际使用 |

### 🖼️ 视觉模型（支持图片输入）

#### 付费视觉模型
| 模型 ID | 描述 | 特点 |
|---------|------|------|
| `openai/gpt-4.1` | GPT-4 Vision | 图片理解、OCR |
| `openai/gpt-4.1-mini` | GPT-4 Mini Vision | 快速视觉处理 |
| `anthropic/claude-opus-4` | Claude Opus 4 | 高级图片分析 |
| `anthropic/claude-sonnet-4` | Claude Sonnet 4 | 平衡的视觉能力 |
| `google/gemini-2.5-pro` | Gemini Pro | 多模态理解 |
| `google/gemini-2.5-flash` | Gemini Flash | 快速图片处理 |
| `x-ai/grok-4` | Grok 4 | 先进视觉理解 |
| `minimax/minimax-01` | MiniMax | 视觉推理 |
| `thudm/glm-4.1v-9b-thinking` | GLM-4 Vision | 思维链视觉 |

#### 免费视觉模型
| 模型 ID | 描述 | 特点 |
|---------|------|------|
| `meta-llama/llama-4-maverick:free` | Llama 4 Maverick | 免费视觉模型 |
| `meta-llama/llama-4-scout:free` | Llama 4 Scout | 基础视觉能力 |
| `moonshotai/kimi-vl-a3b-thinking:free` | Kimi Vision | 视觉思维链 |

## 在 SecondBrain 中使用

### 支持的功能

1. **文本对话**: 所有模型都支持基础的文本对话
2. **多模态输入**: 视觉模型支持图片上传和分析
3. **搜索模式**: 自动使用 Perplexity 模型进行网络搜索
4. **流式响应**: 所有模型都支持实时流式输出
5. **分支对话**: 支持对话分支和版本管理

### 1. 创建对话时选择模型

```json
POST /api/v1/chat/conversations
{
  "title": "我的对话",
  "mode": "chat",  // 可选: "chat" 或 "search"
  "model": "openrouter/auto",  // 推荐使用 auto
  "space_id": null  // 可选：关联到特定空间
}
```

### 2. 发送消息时指定模型

#### 文本消息
```json
POST /api/v1/chat/completions
{
  "conversation_id": 1,
  "messages": [{"role": "user", "content": "你好"}],
  "model": "qwen/qwen3-32b:free",  // 使用免费模型
  "stream": true,  // 可选：启用流式响应
  "temperature": 0.7,  // 可选：控制创造性
  "max_tokens": 2000  // 可选：最大生成长度
}
```

#### 多模态消息（带图片）
```json
POST /api/v1/chat/completions
{
  "conversation_id": 1,
  "messages": [{
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "这张图片中有什么？"
      },
      {
        "type": "image_url",
        "image_url": {
          "url": "data:image/jpeg;base64,/9j/4AAQ..."
        }
      }
    ]
  }],
  "model": "meta-llama/llama-4-scout:free"  // 使用支持视觉的模型
}
```

### 3. 模型选择建议

- **通用推荐**: 使用 `openrouter/auto` - 自动选择最佳模型
- **高级任务**: 
  - 推理: `openai/o1-pro` 或 `deepseek/deepseek-r1-0528:free`
  - 创作: `anthropic/claude-opus-4` 或 `meta-llama/llama-4-maverick:free`
  - 分析: `openai/gpt-4.1` 或 `qwen/qwen3-235b-a22b:free`
- **中文优化**: 
  - 付费: `minimax/minimax-m1` 或 `thudm/glm-4.1v-9b-thinking`
  - 免费: `qwen/qwen3-235b-a22b:free` 或 `moonshotai/kimi-k2:free`
- **代码生成**: 
  - 付费: `openai/gpt-4.1` 或 `anthropic/claude-sonnet-4`
  - 免费: `deepseek/deepseek-chat-v3-0324:free`
- **搜索模式**: 
  - 系统会自动使用 `perplexity/sonar` 或 `perplexity/sonar-pro`（付费用户）

## 费用控制

### 1. 设置预算

在 OpenRouter 控制台设置每月预算限制：
- 访问 [Settings](https://openrouter.ai/settings)
- 设置 "Monthly Budget"

### 2. 使用免费模型

优先使用带 `:free` 后缀的模型，它们完全免费但可能：
- 需要排队等待
- 有速率限制
- 响应速度较慢

### 3. 监控使用量

在 OpenRouter 控制台查看详细的使用统计：
- 模型使用分布
- Token 消耗量
- 费用明细

## 故障排除

### 常见问题

1. **"没有可用的AI提供商"**
   - 检查 `.env` 中是否设置了 `OPENROUTER_API_KEY`
   - 确认 API Key 有效且未过期
   - 重启后端服务使配置生效：
     ```bash
     docker-compose restart backend
     ```

2. **"模型不可用"**
   - 某些免费模型可能暂时不可用（需要排队）
   - 尝试使用 `openrouter/auto` 自动选择
   - 检查模型 ID 是否正确（注意 `:free` 后缀）
   - 运行测试脚本检查可用模型：
     ```bash
     uv run python test_openrouter.py
     ```

3. **"请求超时"**
   - 免费模型可能需要排队
   - 尝试使用付费模型获得更快响应
   - 检查网络连接

4. **"模型不支持图片输入"**
   - 确保使用视觉模型列表中的模型
   - 系统会自动尝试切换到支持的模型
   - 推荐使用 `openrouter/auto` 自动选择

5. **"达到速率限制"**
   - 免费模型有请求频率限制
   - 等待几分钟后重试
   - 考虑升级到付费模型

### 测试命令

```bash
# 测试 OpenRouter 连接
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# 测试简单对话（使用当前可用的免费模型）
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3-32b:free",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# 测试 auto 模型
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openrouter/auto",
    "messages": [{"role": "user", "content": "What is 2+2?"}]
  }'
```

## 最佳实践

1. **开发阶段**：
   - 使用免费模型节省成本
   - 推荐：`qwen/qwen3-32b:free`（稳定性好）
   - 备选：`deepseek/deepseek-chat-v3-0324:free`（代码任务）

2. **生产环境**：
   - 默认使用 `openrouter/auto` 自动优化
   - 搜索模式会自动使用 Perplexity 模型
   - 视觉内容会自动切换到支持的模型

3. **特定任务**：
   - 代码审查：`deepseek/deepseek-r1-0528:free`
   - 长文本：`moonshotai/kimi-k2:free`
   - 中文任务：`qwen/qwen3-235b-a22b:free`
   - 创意写作：`meta-llama/llama-4-maverick:free`

4. **性能优化**：
   - 启用流式响应提升用户体验
   - 合理设置 `max_tokens` 控制成本
   - 使用 `temperature` 参数平衡创造性和准确性

5. **监控使用**：
   - 定期检查 OpenRouter 控制台的使用统计
   - 设置预算提醒避免超支
   - 记录模型使用情况优化选择

## 更多资源

- [OpenRouter 官方文档](https://openrouter.ai/docs)
- [模型对比](https://openrouter.ai/models)
- [API 参考](https://openrouter.ai/docs/api)
- [定价信息](https://openrouter.ai/pricing)

## 附录：模型特性对照表

| 特性 | 免费模型 | 付费模型 | OpenRouter Auto |
|------|----------|----------|----------------|
| 响应速度 | 中等（需排队） | 快速 | 自动优化 |
| 上下文长度 | 4K-32K | 8K-200K | 根据模型 |
| 视觉能力 | 部分支持 | 全面支持 | 自动检测 |
| 搜索功能 | 不支持 | 部分支持 | 自动切换 |
| 成本 | 免费 | 按用量计费 | 动态定价 |
| 稳定性 | 一般 | 高 | 高 |
| 适用场景 | 开发测试 | 生产环境 | 所有场景 |