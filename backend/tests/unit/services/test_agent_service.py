"""Unit tests for Agent Service."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.services.agent_service import AgentService, AgentTemplate


@pytest.fixture
def agent_service():
    """创建代理服务实例."""
    return AgentService()


@pytest.fixture
def mock_ai_service():
    """创建模拟AI服务."""
    mock_service = Mock()
    mock_service.chat = AsyncMock()
    return mock_service


@pytest.fixture
def sample_agent_template():
    """创建示例代理模板."""
    return AgentTemplate(
        id="test_agent",
        name="Test Agent",
        description="A test agent",
        type="analysis",
        prompt="You are a test agent",
        model="gpt-4",
        temperature=0.7,
        max_tokens=1000,
        tools=["analysis"],
        settings={"test": True},
        tags=["test"],
        category="test"
    )


class TestAgentService:
    """测试代理服务."""

    def test_init(self, agent_service):
        """测试初始化."""
        assert agent_service.ai_service is not None
        assert len(agent_service.agent_templates) == 5
        assert all(isinstance(template, AgentTemplate) for template in agent_service.agent_templates)

    @pytest.mark.asyncio
    async def test_get_agent_templates(self, agent_service):
        """测试获取代理模板."""
        templates = await agent_service.get_agent_templates()

        assert len(templates) == 5
        assert all(isinstance(template, AgentTemplate) for template in templates)

        # 检查是否包含预期的模板
        template_ids = [template.id for template in templates]
        expected_ids = ["data_analyst", "content_writer", "research_assistant", "code_reviewer", "customer_service"]
        assert all(tid in template_ids for tid in expected_ids)

    @pytest.mark.asyncio
    async def test_get_agent_template_found(self, agent_service):
        """测试获取指定代理模板（找到）."""
        template = await agent_service.get_agent_template("data_analyst")

        assert template is not None
        assert template.id == "data_analyst"
        assert template.name == "数据分析师"
        assert template.type == "analysis"

    @pytest.mark.asyncio
    async def test_get_agent_template_not_found(self, agent_service):
        """测试获取指定代理模板（未找到）."""
        template = await agent_service.get_agent_template("non_existent")

        assert template is None

    @pytest.mark.asyncio
    async def test_execute_agent_success(self, agent_service, sample_agent_template):
        """测试成功执行代理."""
        # Mock AI service response
        mock_response = "Test response content"
        agent_service.ai_service.chat = AsyncMock(return_value=mock_response)

        input_data = {"message": "Test input"}
        parameters = {"temperature": 0.5}
        user = Mock()

        result = await agent_service.execute_agent(
            sample_agent_template, input_data, parameters, user
        )

        assert result["status"] == "completed"
        assert result["output"]["content"] == mock_response
        assert result["output"]["type"] == "analysis"
        assert "processing_time" in result
        assert "completed_at" in result
        assert result["metadata"]["agent_type"] == "analysis"
        assert result["metadata"]["agent_tools"] == ["analysis"]

    @pytest.mark.asyncio
    async def test_execute_agent_with_parameters(self, agent_service, sample_agent_template):
        """测试带参数执行代理."""
        mock_response = "Test response"
        agent_service.ai_service.chat = AsyncMock(return_value=mock_response)

        input_data = {"message": "Test input"}
        parameters = {
            "temperature": 0.3,
            "max_tokens": 500,
            "model": "gpt-3.5-turbo"
        }
        user = Mock()

        result = await agent_service.execute_agent(
            sample_agent_template, input_data, parameters, user
        )

        # 验证结果
        assert result["status"] == "completed"

        # 验证调用参数
        agent_service.ai_service.chat.assert_called_once()
        call_args = agent_service.ai_service.chat.call_args
        assert call_args[1]["temperature"] == 0.3
        assert call_args[1]["max_tokens"] == 500
        assert call_args[1]["model"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_execute_agent_failure(self, agent_service, sample_agent_template):
        """测试代理执行失败."""
        # Mock AI service to raise exception
        agent_service.ai_service.chat = AsyncMock(side_effect=Exception("AI service error"))

        input_data = {"message": "Test input"}
        parameters = {}
        user = Mock()

        result = await agent_service.execute_agent(
            sample_agent_template, input_data, parameters, user
        )

        assert result["status"] == "failed"
        assert result["error"] == "AI service error"
        assert "processing_time" in result
        assert "completed_at" in result

    @pytest.mark.asyncio
    async def test_execute_agent_async_success(self, agent_service, sample_agent_template):
        """测试异步执行代理成功."""
        # Mock execute_agent method
        mock_result = {
            "status": "completed",
            "output": {"content": "Test output"},
            "processing_time": 1.5,
            "completed_at": "2023-01-01T00:00:00"
        }
        agent_service.execute_agent = AsyncMock(return_value=mock_result)

        # Mock execution and db
        mock_execution = Mock()
        mock_execution.input_data = {"message": "Test input"}
        mock_execution.parameters = {"temperature": 0.7}
        mock_db = Mock()
        mock_db.commit = AsyncMock()

        await agent_service.execute_agent_async(
            sample_agent_template, mock_execution, mock_db
        )

        # 验证结果被设置
        assert mock_execution.output_data == {"content": "Test output"}
        assert mock_execution.status == "completed"
        assert mock_execution.processing_time == 1.5
        assert mock_execution.completed_at == "2023-01-01T00:00:00"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_agent_async_failure(self, agent_service, sample_agent_template):
        """测试异步执行代理失败."""
        # Mock execute_agent to raise exception
        agent_service.execute_agent = AsyncMock(side_effect=Exception("Execution error"))

        mock_execution = Mock()
        mock_execution.input_data = {"message": "Test input"}
        mock_execution.parameters = {}
        mock_db = Mock()
        mock_db.commit = AsyncMock()

        await agent_service.execute_agent_async(
            sample_agent_template, mock_execution, mock_db
        )

        # 验证错误处理
        assert mock_execution.status == "failed"
        assert mock_execution.error_message == "Execution error"
        assert mock_execution.completed_at is not None
        mock_db.commit.assert_called_once()


class TestFormatInputMessage:
    """测试格式化输入消息."""

    def test_format_input_message_basic(self, agent_service):
        """测试基本消息格式化."""
        input_data = {"message": "Test message"}
        result = agent_service._format_input_message(input_data, "general")

        assert result == "Test message"

    def test_format_input_message_analysis(self, agent_service):
        """测试分析类型消息格式化."""
        input_data = {"message": "Analyze this", "data": "Sample data"}
        result = agent_service._format_input_message(input_data, "analysis")

        assert "请分析以下数据" in result
        assert "Sample data" in result
        assert "Analyze this" in result

    def test_format_input_message_writing(self, agent_service):
        """测试写作类型消息格式化."""
        input_data = {"message": "Write an article", "style": "formal"}
        result = agent_service._format_input_message(input_data, "writing")

        assert "写作要求：Write an article" in result
        assert "写作风格：formal" in result

    def test_format_input_message_research(self, agent_service):
        """测试研究类型消息格式化."""
        input_data = {"message": "Research this topic", "topic": "AI research"}
        result = agent_service._format_input_message(input_data, "research")

        assert "研究主题：AI research" in result
        assert "Research this topic" in result

    def test_format_input_message_development(self, agent_service):
        """测试开发类型消息格式化."""
        input_data = {"message": "Review this code", "code": "def test(): pass"}
        result = agent_service._format_input_message(input_data, "development")

        assert "请审查以下代码" in result
        assert "def test(): pass" in result
        assert "Review this code" in result

    def test_format_input_message_support(self, agent_service):
        """测试支持类型消息格式化."""
        input_data = {"message": "Help with issue", "issue": "Login problem"}
        result = agent_service._format_input_message(input_data, "support")

        assert "客户问题：Login problem" in result
        assert "Help with issue" in result

    def test_format_input_message_text_field(self, agent_service):
        """测试使用text字段的消息格式化."""
        input_data = {"text": "Test text"}
        result = agent_service._format_input_message(input_data, "general")

        assert result == "Test text"

    def test_format_input_message_content_field(self, agent_service):
        """测试使用content字段的消息格式化."""
        input_data = {"content": "Test content"}
        result = agent_service._format_input_message(input_data, "general")

        assert result == "Test content"

    def test_format_input_message_fallback(self, agent_service):
        """测试回退到字符串转换."""
        input_data = {"other": "value"}
        result = agent_service._format_input_message(input_data, "general")

        assert "other" in result
        assert "value" in result


class TestFormatOutputData:
    """测试格式化输出数据."""

    def test_format_output_data_basic(self, agent_service):
        """测试基本输出格式化."""
        content = "Test output content"
        result = agent_service._format_output_data(content, "general")

        assert result["content"] == content
        assert result["type"] == "general"
        assert "generated_at" in result

    def test_format_output_data_analysis(self, agent_service):
        """测试分析类型输出格式化."""
        content = "发现了一个重要趋势。建议采取行动。"
        result = agent_service._format_output_data(content, "analysis")

        assert result["analysis_type"] == "general"
        assert "insights" in result
        assert "recommendations" in result
        assert len(result["insights"]) > 0
        assert len(result["recommendations"]) > 0

    def test_format_output_data_writing(self, agent_service):
        """测试写作类型输出格式化."""
        content = "This is a test article with multiple words."
        result = agent_service._format_output_data(content, "writing")

        assert result["word_count"] == 8
        assert result["writing_style"] == "professional"
        assert result["content_type"] == "article"

    def test_format_output_data_research(self, agent_service):
        """测试研究类型输出格式化."""
        content = "研究发现了重要结果。参考链接：https://example.com"
        result = agent_service._format_output_data(content, "research")

        assert result["research_depth"] == "comprehensive"
        assert "sources_mentioned" in result
        assert "key_findings" in result
        assert len(result["sources_mentioned"]) > 0

    def test_format_output_data_development(self, agent_service):
        """测试开发类型输出格式化."""
        content = "代码中存在问题。建议改进性能。"
        result = agent_service._format_output_data(content, "development")

        assert result["review_type"] == "code_quality"
        assert "issues_found" in result
        assert "suggestions" in result
        assert len(result["issues_found"]) > 0

    def test_format_output_data_support(self, agent_service):
        """测试支持类型输出格式化."""
        content = "问题已解决。如需后续支持，请联系我们。"
        result = agent_service._format_output_data(content, "support")

        assert result["support_type"] == "general"
        assert result["resolution_provided"] is True
        assert result["follow_up_needed"] is True  # 因为包含"后续"


class TestExtractMethods:
    """测试提取方法."""

    def test_extract_insights(self, agent_service):
        """测试提取洞察."""
        content = "这是一个重要发现。\n分析显示了明显的趋势。\n数据模式很清晰。"
        insights = agent_service._extract_insights(content)

        assert len(insights) == 3
        assert "重要发现" in insights[0]
        assert "趋势" in insights[1]
        assert "模式" in insights[2]

    def test_extract_recommendations(self, agent_service):
        """测试提取建议."""
        content = "我建议采取行动。\n推荐使用新方法。\n应该考虑其他选择。"
        recommendations = agent_service._extract_recommendations(content)

        assert len(recommendations) == 3
        assert "建议" in recommendations[0]
        assert "推荐" in recommendations[1]
        assert "应该" in recommendations[2]

    def test_extract_sources(self, agent_service):
        """测试提取来源."""
        content = "参考链接：https://example.com 和 https://test.org"
        sources = agent_service._extract_sources(content)

        assert len(sources) == 2
        assert "https://example.com" in sources
        assert "https://test.org" in sources

    def test_extract_key_findings(self, agent_service):
        """测试提取关键发现."""
        content = "研究发现了重要结果。\n结论是明确的。\n显示了积极的趋势。"
        findings = agent_service._extract_key_findings(content)

        assert len(findings) == 3
        assert "发现" in findings[0]
        assert "结论" in findings[1]
        assert "显示" in findings[2]

    def test_extract_issues(self, agent_service):
        """测试提取问题."""
        content = "代码中存在问题。\n发现了一个错误。\n需要改进性能。"
        issues = agent_service._extract_issues(content)

        assert len(issues) == 3
        assert "问题" in issues[0]
        assert "错误" in issues[1]
        assert "改进" in issues[2]

    def test_extract_suggestions(self, agent_service):
        """测试提取建议."""
        content = "建议优化代码。\n可以改进算法。\n应该重构函数。"
        suggestions = agent_service._extract_suggestions(content)

        assert len(suggestions) == 2
        assert "建议" in suggestions[0]
        assert "可以" in suggestions[1]

    def test_check_follow_up_needed_true(self, agent_service):
        """测试检查需要后续跟进（是）."""
        content = "问题已解决，如需后续支持请联系。"
        result = agent_service._check_follow_up_needed(content)

        assert result is True

    def test_check_follow_up_needed_false(self, agent_service):
        """测试检查需要后续跟进（否）."""
        content = "问题已完全解决。"
        result = agent_service._check_follow_up_needed(content)

        assert result is False


class TestValidateAgentConfig:
    """测试验证代理配置."""

    @pytest.mark.asyncio
    async def test_validate_agent_config_valid(self, agent_service):
        """测试有效的代理配置."""
        config = {
            "name": "Test Agent",
            "type": "analysis",
            "prompt": "You are a test agent",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await agent_service.validate_agent_config(config)

        assert result["valid"] is True
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_agent_config_missing_fields(self, agent_service):
        """测试缺少字段的配置."""
        config = {
            "name": "Test Agent",
            "type": "analysis"
        }

        result = await agent_service.validate_agent_config(config)

        assert result["valid"] is False
        assert len(result["issues"]) == 2
        assert "缺少必需字段: prompt" in result["issues"]
        assert "缺少必需字段: model" in result["issues"]

    @pytest.mark.asyncio
    async def test_validate_agent_config_invalid_model(self, agent_service):
        """测试无效模型的配置."""
        config = {
            "name": "Test Agent",
            "type": "analysis",
            "prompt": "You are a test agent",
            "model": "invalid-model",
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await agent_service.validate_agent_config(config)

        assert result["valid"] is False
        assert "无效的模型: invalid-model" in result["issues"]

    @pytest.mark.asyncio
    async def test_validate_agent_config_invalid_temperature(self, agent_service):
        """测试无效温度的配置."""
        config = {
            "name": "Test Agent",
            "type": "analysis",
            "prompt": "You are a test agent",
            "model": "gpt-4",
            "temperature": 3.0,
            "max_tokens": 2000
        }

        result = await agent_service.validate_agent_config(config)

        assert result["valid"] is False
        assert "温度参数必须在0-2之间" in result["issues"]

    @pytest.mark.asyncio
    async def test_validate_agent_config_invalid_max_tokens(self, agent_service):
        """测试无效token数的配置."""
        config = {
            "name": "Test Agent",
            "type": "analysis",
            "prompt": "You are a test agent",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 10000
        }

        result = await agent_service.validate_agent_config(config)

        assert result["valid"] is False
        assert "最大token数必须在1-8000之间" in result["issues"]


class TestGetAgentCapabilities:
    """测试获取代理能力."""

    @pytest.mark.asyncio
    async def test_get_agent_capabilities_analysis(self, agent_service):
        """测试获取分析代理能力."""
        capabilities = await agent_service.get_agent_capabilities("analysis")

        assert capabilities["description"] == "数据分析和统计处理"
        assert "csv" in capabilities["supported_formats"]
        assert "insights" in capabilities["output_types"]
        assert "data_analysis" in capabilities["tools"]

    @pytest.mark.asyncio
    async def test_get_agent_capabilities_writing(self, agent_service):
        """测试获取写作代理能力."""
        capabilities = await agent_service.get_agent_capabilities("writing")

        assert capabilities["description"] == "内容创作和编辑"
        assert "markdown" in capabilities["supported_formats"]
        assert "articles" in capabilities["output_types"]
        assert "writing" in capabilities["tools"]

    @pytest.mark.asyncio
    async def test_get_agent_capabilities_research(self, agent_service):
        """测试获取研究代理能力."""
        capabilities = await agent_service.get_agent_capabilities("research")

        assert capabilities["description"] == "信息研究和分析"
        assert "urls" in capabilities["supported_formats"]
        assert "reports" in capabilities["output_types"]
        assert "search" in capabilities["tools"]

    @pytest.mark.asyncio
    async def test_get_agent_capabilities_development(self, agent_service):
        """测试获取开发代理能力."""
        capabilities = await agent_service.get_agent_capabilities("development")

        assert capabilities["description"] == "代码审查和开发支持"
        assert "code" in capabilities["supported_formats"]
        assert "reviews" in capabilities["output_types"]
        assert "code_analysis" in capabilities["tools"]

    @pytest.mark.asyncio
    async def test_get_agent_capabilities_support(self, agent_service):
        """测试获取支持代理能力."""
        capabilities = await agent_service.get_agent_capabilities("support")

        assert capabilities["description"] == "客户服务和支持"
        assert "chat" in capabilities["supported_formats"]
        assert "solutions" in capabilities["output_types"]
        assert "support" in capabilities["tools"]

    @pytest.mark.asyncio
    async def test_get_agent_capabilities_unknown(self, agent_service):
        """测试获取未知类型代理能力."""
        capabilities = await agent_service.get_agent_capabilities("unknown")

        assert capabilities["description"] == "通用AI助手"
        assert capabilities["supported_formats"] == ["text"]
        assert capabilities["output_types"] == ["responses"]
        assert capabilities["tools"] == ["general"]


class TestGlobalInstance:
    """测试全局实例."""

    def test_global_instance_exists(self):
        """测试全局实例存在."""
        from app.services.agent_service import agent_service

        assert isinstance(agent_service, AgentService)
        assert hasattr(agent_service, 'execute_agent')
        assert hasattr(agent_service, 'get_agent_templates')
        assert hasattr(agent_service, 'validate_agent_config')
        assert hasattr(agent_service, 'get_agent_capabilities')
