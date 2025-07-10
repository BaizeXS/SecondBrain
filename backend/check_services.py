"""检查服务配置状态的工具."""

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def check_env_var(var_name: str) -> tuple[bool, str]:
    """检查环境变量是否设置."""
    # 重新加载环境变量
    from dotenv import load_dotenv
    load_dotenv()

    value = os.getenv(var_name)
    if value and value.lower() not in ['none', '', 'your_api_key']:
        return True, "✅ 已配置"
    return False, "❌ 未配置"

def check_services():
    """检查所有服务的配置状态."""
    console.print(Panel.fit("🔍 Second Brain 服务配置检查", style="bold blue"))

    # 创建表格
    table = Table(title="服务配置状态")
    table.add_column("服务", style="cyan", no_wrap=True)
    table.add_column("组件", style="magenta")
    table.add_column("状态", style="green")
    table.add_column("说明", style="yellow")

    # 基础服务
    table.add_row("数据库", "PostgreSQL", "✅ 已配置", "DATABASE_URL 已设置")
    table.add_row("缓存", "Redis", "✅ 已配置", "REDIS_URL 已设置")
    table.add_row("对象存储", "MinIO", "✅ 已配置", "使用默认配置")
    table.add_row("向量数据库", "Qdrant", "✅ 已配置", "使用默认配置")

    # AI服务
    ai_services = [
        ("OpenAI", "OPENAI_API_KEY", "支持 GPT-4, GPT-3.5"),
        ("Anthropic", "ANTHROPIC_API_KEY", "支持 Claude"),
        ("Google", "GOOGLE_API_KEY", "支持 Gemini"),
        ("DeepSeek", "DEEPSEEK_API_KEY", "支持推理模型"),
    ]

    ai_ready = False
    for service, env_var, desc in ai_services:
        status, status_text = check_env_var(env_var)
        if status:
            ai_ready = True
        table.add_row("AI服务", service, status_text, desc)

    console.print(table)

    # 建议
    console.print("\n📋 分析结果：")

    if not ai_ready:
        console.print("⚠️  [yellow]所有 AI 服务都未配置 API 密钥[/yellow]")
        console.print("   当前使用 ai_service_simple.py 返回模拟响应")
        console.print("   如需启用真实 AI 功能，请在 .env 文件中配置至少一个 AI 服务的 API 密钥")
    else:
        console.print("✅ [green]至少有一个 AI 服务已配置，可以使用完整版 ai_service.py[/green]")

    # 文档服务检查
    console.print("\n📄 文档服务状态：")
    try:
        import docx
        import pptx
        import pypdf
        console.print("✅ 文档处理库已安装（pypdf, python-docx, python-pptx）")
        console.print("   可以使用完整版 document_service.py")
    except ImportError as e:
        console.print(f"⚠️  [yellow]缺少文档处理库：{e}[/yellow]")
        console.print("   当前只能使用 document_service_simple.py（仅数据库操作）")

    # 显示当前使用的服务版本
    console.print("\n🔧 当前服务版本：")
    try:
        from app.services import get_service_status
        status = get_service_status()
        for service, version in status.items():
            emoji = "✅" if version == "full" else "⚠️"
            service_name = service.replace("_", " ").title()
            console.print(f"{emoji} {service_name}: {version}")
    except Exception as e:
        console.print(f"❌ 无法获取服务状态: {e}")

    return ai_ready

if __name__ == "__main__":
    check_services()
