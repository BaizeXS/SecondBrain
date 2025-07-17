"""AI Agent execution service."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.services.ai_service import AIService

logger = logging.getLogger(__name__)


@dataclass
class AgentTemplate:
    """Agent template for service usage."""
    id: str
    name: str
    description: str
    type: str
    prompt: str
    model: str
    temperature: float
    max_tokens: int
    tools: list[str]
    settings: dict[str, Any]
    tags: list[str]
    category: str


class AgentService:
    """AI代理执行服务."""

    def __init__(self) -> None:
        """初始化代理服务."""
        self.ai_service = AIService()
        self.agent_templates = self._load_agent_templates()

    def _load_agent_templates(self) -> list[AgentTemplate]:
        """加载代理模板."""
        templates = [
            AgentTemplate(
                id="data_analyst",
                name="数据分析师",
                description="专业的数据分析和可视化助手，能够处理各种数据分析任务",
                type="analysis",
                prompt="""你是一个专业的数据分析师。你的任务是：
1. 分析用户提供的数据
2. 识别数据中的模式和趋势
3. 提供有价值的洞察和建议
4. 如果需要，建议合适的可视化方法

请保持专业、准确，并用清晰易懂的语言解释你的发现。""",
                model="gpt-4",
                temperature=0.3,
                max_tokens=2000,
                tools=["data_analysis", "visualization"],
                settings={
                    "analysis_depth": "detailed",
                    "include_recommendations": True,
                    "visualization_suggestions": True,
                },
                tags=["数据分析", "统计", "可视化"],
                category="分析工具",
            ),
            AgentTemplate(
                id="content_writer",
                name="内容创作者",
                description="专业的内容创作助手，擅长各种文体的写作和编辑",
                type="writing",
                prompt="""你是一个专业的内容创作者。你的能力包括：
1. 创作各种类型的文章和文档
2. 编辑和改进现有内容
3. 调整写作风格以适应不同受众
4. 确保内容的逻辑性和可读性

请根据用户的需求，提供高质量、有价值的内容。""",
                model="gpt-4",
                temperature=0.7,
                max_tokens=3000,
                tools=["writing", "editing"],
                settings={
                    "writing_style": "professional",
                    "tone": "friendly",
                    "include_examples": True,
                },
                tags=["写作", "编辑", "内容创作"],
                category="创作工具",
            ),
            AgentTemplate(
                id="research_assistant",
                name="研究助手",
                description="专业的研究助手，能够进行深度信息搜集和分析",
                type="research",
                prompt="""你是一个专业的研究助手。你的职责是：
1. 深入研究用户指定的主题
2. 收集和整理相关信息
3. 分析信息的可靠性和相关性
4. 提供结构化的研究报告

请确保信息的准确性，并提供可验证的来源。""",
                model="gpt-4",
                temperature=0.4,
                max_tokens=4000,
                tools=["search", "analysis"],
                settings={
                    "research_depth": "comprehensive",
                    "include_sources": True,
                    "fact_checking": True,
                },
                tags=["研究", "信息收集", "分析"],
                category="研究工具",
            ),
            AgentTemplate(
                id="code_reviewer",
                name="代码审查员",
                description="专业的代码审查助手，提供代码质量分析和改进建议",
                type="development",
                prompt="""你是一个专业的代码审查员。你的任务是：
1. 分析代码的质量和结构
2. 识别潜在的bug和性能问题
3. 提供改进建议和最佳实践
4. 确保代码符合编程规范

请提供具体、可操作的反馈和建议。""",
                model="gpt-4",
                temperature=0.2,
                max_tokens=2500,
                tools=["code_analysis", "debugging"],
                settings={
                    "review_depth": "thorough",
                    "include_examples": True,
                    "performance_analysis": True,
                },
                tags=["代码审查", "编程", "质量控制"],
                category="开发工具",
            ),
            AgentTemplate(
                id="customer_service",
                name="客服助手",
                description="专业的客户服务助手，提供友好和有效的客户支持",
                type="support",
                prompt="""你是一个专业的客服助手。你的目标是：
1. 理解客户的问题和需求
2. 提供准确、有用的解决方案
3. 保持友好、耐心的服务态度
4. 确保客户满意度

请始终以客户为中心，提供优质的服务体验。""",
                model="gpt-3.5-turbo",
                temperature=0.6,
                max_tokens=1500,
                tools=["support", "knowledge_base"],
                settings={
                    "response_style": "friendly",
                    "empathy_level": "high",
                    "solution_focused": True,
                },
                tags=["客服", "支持", "沟通"],
                category="服务工具",
            ),
        ]

        return templates

    async def get_agent_templates(self) -> list[AgentTemplate]:
        """获取所有代理模板."""
        return self.agent_templates

    async def get_agent_template(self, template_id: str) -> AgentTemplate | None:
        """获取指定的代理模板."""
        for template in self.agent_templates:
            if template.id == template_id:
                return template
        return None

    async def execute_agent(
        self, agent: AgentTemplate, input_data: dict[str, Any], parameters: dict[str, Any], user: Any
    ) -> dict[str, Any]:
        """执行AI代理."""
        start_time = time.time()

        try:
            # 构建提示词
            system_prompt = agent.prompt

            # 处理输入数据
            user_message = self._format_input_message(input_data, agent.type)

            # 准备消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            # 应用参数设置
            temperature = parameters.get("temperature", agent.temperature)
            max_tokens = parameters.get("max_tokens", agent.max_tokens)
            model = parameters.get("model", agent.model)

            # 调用AI服务
            response = await self.ai_service.chat(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                user=user,
            )

            # 处理输出
            output_data = self._format_output_data(response, agent.type)

            processing_time = time.time() - start_time

            return {
                "status": "completed",
                "output": output_data,
                "processing_time": processing_time,
                "completed_at": datetime.utcnow(),
                "metadata": {
                    "model_used": model,
                    "token_count": getattr(response, 'token_count', 0),
                    "agent_type": agent.type,
                    "agent_tools": agent.tools,
                },
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"代理执行失败: {str(e)}")

            return {
                "status": "failed",
                "error": str(e),
                "processing_time": processing_time,
                "completed_at": datetime.utcnow(),
            }

    async def execute_agent_async(self, agent: AgentTemplate, execution: Any, db: Any) -> None:
        """异步执行代理（后台任务）."""
        try:
            # 获取输入数据
            input_data = execution.input_data
            parameters = execution.parameters or {}

            # 执行代理
            result = await self.execute_agent(
                agent,
                input_data,
                parameters,
                None,  # 后台任务中用户信息可能不可用
            )

            # 更新执行记录
            execution.output_data = result.get("output")
            execution.status = result.get("status", "completed")
            execution.error_message = result.get("error")
            execution.processing_time = result.get("processing_time")
            execution.completed_at = result.get("completed_at")

            await db.commit()

        except Exception as e:
            logger.error(f"异步代理执行失败: {str(e)}")

            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()

            await db.commit()

    def _format_input_message(self, input_data: dict[str, Any], agent_type: str) -> str:
        """格式化输入消息."""
        if "message" in input_data:
            base_message = input_data["message"]
        elif "text" in input_data:
            base_message = input_data["text"]
        elif "content" in input_data:
            base_message = input_data["content"]
        else:
            base_message = str(input_data)

        # 根据代理类型添加特定的上下文
        if agent_type == "analysis":
            if "data" in input_data:
                return f"请分析以下数据：\n\n{input_data['data']}\n\n具体要求：{base_message}"
            else:
                return f"数据分析任务：{base_message}"

        elif agent_type == "writing":
            if "style" in input_data:
                return f"写作要求：{base_message}\n\n写作风格：{input_data['style']}"
            else:
                return f"写作任务：{base_message}"

        elif agent_type == "research":
            if "topic" in input_data:
                return f"研究主题：{input_data['topic']}\n\n具体要求：{base_message}"
            else:
                return f"研究任务：{base_message}"

        elif agent_type == "development":
            if "code" in input_data:
                return f"请审查以下代码：\n\n```\n{input_data['code']}\n```\n\n审查要求：{base_message}"
            else:
                return f"开发任务：{base_message}"

        elif agent_type == "support":
            if "issue" in input_data:
                return f"客户问题：{input_data['issue']}\n\n处理要求：{base_message}"
            else:
                return f"客服任务：{base_message}"

        return base_message

    def _format_output_data(self, content: str, agent_type: str) -> dict[str, Any]:
        """格式化输出数据."""
        base_output: dict[str, Any] = {
            "content": content,
            "type": agent_type,
            "generated_at": datetime.utcnow().isoformat(),
        }

        # 尝试提取结构化信息
        if agent_type == "analysis":
            base_output["analysis_type"] = "general"
            base_output["insights"] = self._extract_insights(content)
            base_output["recommendations"] = self._extract_recommendations(content)

        elif agent_type == "writing":
            base_output["word_count"] = len(content.split())
            base_output["writing_style"] = "professional"
            base_output["content_type"] = "article"

        elif agent_type == "research":
            base_output["research_depth"] = "comprehensive"
            base_output["sources_mentioned"] = self._extract_sources(content)
            base_output["key_findings"] = self._extract_key_findings(content)

        elif agent_type == "development":
            base_output["review_type"] = "code_quality"
            base_output["issues_found"] = self._extract_issues(content)
            base_output["suggestions"] = self._extract_suggestions(content)

        elif agent_type == "support":
            base_output["support_type"] = "general"
            base_output["resolution_provided"] = True
            base_output["follow_up_needed"] = self._check_follow_up_needed(content)

        return base_output

    def _extract_insights(self, content: str) -> list[str]:
        """提取分析洞察."""
        # 简化的洞察提取逻辑
        insights = []
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower() for keyword in ["发现", "洞察", "趋势", "模式"]
            ):
                insights.append(line.strip())
        return insights[:5]  # 最多返回5个洞察

    def _extract_recommendations(self, content: str) -> list[str]:
        """提取建议."""
        recommendations = []
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower() for keyword in ["建议", "推荐", "应该", "可以"]
            ):
                recommendations.append(line.strip())
        return recommendations[:5]

    def _extract_sources(self, content: str) -> list[str]:
        """提取来源."""
        # 简化的来源提取逻辑
        import re

        sources = re.findall(r"https?://[^\s]+", content)
        return sources[:10]  # 最多返回10个来源

    def _extract_key_findings(self, content: str) -> list[str]:
        """提取关键发现."""
        findings = []
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower() for keyword in ["发现", "结果", "结论", "显示"]
            ):
                findings.append(line.strip())
        return findings[:5]

    def _extract_issues(self, content: str) -> list[str]:
        """提取代码问题."""
        issues = []
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower() for keyword in ["问题", "错误", "bug", "改进"]
            ):
                issues.append(line.strip())
        return issues[:10]

    def _extract_suggestions(self, content: str) -> list[str]:
        """提取改进建议."""
        suggestions = []
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line.lower() for keyword in ["建议", "优化", "改进", "可以"]
            ):
                suggestions.append(line.strip())
        return suggestions[:10]

    def _check_follow_up_needed(self, content: str) -> bool:
        """检查是否需要后续跟进."""
        follow_up_keywords = ["后续", "跟进", "联系", "进一步", "稍后"]
        return any(keyword in content.lower() for keyword in follow_up_keywords)

    async def validate_agent_config(
        self, agent_config: dict[str, Any]
    ) -> dict[str, Any]:
        """验证代理配置."""
        issues = []

        # 检查必需字段
        required_fields = ["name", "type", "prompt", "model"]
        for field in required_fields:
            if not agent_config.get(field):
                issues.append(f"缺少必需字段: {field}")

        # 检查模型有效性（只有在模型存在时才检查）
        valid_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "gemini-pro"]
        model = agent_config.get("model")
        if model and model not in valid_models:
            issues.append(f"无效的模型: {model}")

        # 检查温度参数
        temperature = agent_config.get("temperature", 0.7)
        if not 0 <= temperature <= 2:
            issues.append("温度参数必须在0-2之间")

        # 检查最大token数
        max_tokens = agent_config.get("max_tokens", 2000)
        if not 1 <= max_tokens <= 8000:
            issues.append("最大token数必须在1-8000之间")

        return {"valid": len(issues) == 0, "issues": issues}

    async def get_agent_capabilities(self, agent_type: str) -> dict[str, Any]:
        """获取代理类型的能力描述."""
        capabilities = {
            "analysis": {
                "description": "数据分析和统计处理",
                "supported_formats": ["csv", "json", "text"],
                "output_types": ["insights", "recommendations", "visualizations"],
                "tools": ["data_analysis", "statistics", "visualization"],
            },
            "writing": {
                "description": "内容创作和编辑",
                "supported_formats": ["text", "markdown", "html"],
                "output_types": ["articles", "reports", "summaries"],
                "tools": ["writing", "editing", "proofreading"],
            },
            "research": {
                "description": "信息研究和分析",
                "supported_formats": ["text", "urls", "documents"],
                "output_types": ["reports", "summaries", "citations"],
                "tools": ["search", "analysis", "fact_checking"],
            },
            "development": {
                "description": "代码审查和开发支持",
                "supported_formats": ["code", "text"],
                "output_types": ["reviews", "suggestions", "fixes"],
                "tools": ["code_analysis", "debugging", "optimization"],
            },
            "support": {
                "description": "客户服务和支持",
                "supported_formats": ["text", "chat"],
                "output_types": ["solutions", "guides", "responses"],
                "tools": ["support", "knowledge_base", "escalation"],
            },
        }

        return capabilities.get(
            agent_type,
            {
                "description": "通用AI助手",
                "supported_formats": ["text"],
                "output_types": ["responses"],
                "tools": ["general"],
            },
        )


# 创建全局实例
agent_service = AgentService()
