#!/usr/bin/env python3
"""
SecondBrain API 性能测试套件
用于测试API的性能、并发能力和稳定性
"""

import asyncio
import json
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户
TEST_USER = {
    "username": "perf_test_user",
    "email": "perf_test@example.com",
    "password": "PerfTest123!",
}


class PerformanceTestSuite:
    """性能测试套件"""

    def __init__(self):
        self.results = {
            "summary": {},
            "endpoints": {},
            "scenarios": {},
            "errors": [],
        }
        self.access_token = None
        self.space_id = None
        self.document_id = None
        self.conversation_id = None

    async def __aenter__(self):
        """初始化测试环境"""
        self.session = aiohttp.ClientSession()
        await self.setup_test_data()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """清理测试环境"""
        await self.cleanup_test_data()
        await self.session.close()

    async def setup_test_data(self):
        """设置测试数据"""
        print("🔧 设置测试环境...")

        # 尝试登录，如果失败则注册
        try:
            await self.login()
        except:
            await self.register()
            await self.login()

        # 创建测试空间
        await self.create_test_space()

    async def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        # 实际清理逻辑可以根据需要实现

    async def register(self):
        """注册测试用户"""
        async with self.session.post(
            f"{API_BASE}/auth/register",
            json={
                "username": TEST_USER["username"],
                "email": TEST_USER["email"],
                "password": TEST_USER["password"],
                "full_name": "Performance Test User",
            },
        ) as resp:
            if resp.status != 201:
                raise Exception(f"注册失败: {await resp.text()}")

    async def login(self):
        """登录获取token"""
        data = aiohttp.FormData()
        data.add_field("username", TEST_USER["username"])
        data.add_field("password", TEST_USER["password"])

        async with self.session.post(f"{API_BASE}/auth/login", data=data) as resp:
            if resp.status != 200:
                raise Exception(f"登录失败: {await resp.text()}")
            result = await resp.json()
            self.access_token = result["access_token"]
            # 更新session headers
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})

    async def create_test_space(self):
        """创建测试空间"""
        async with self.session.post(
            f"{API_BASE}/spaces",
            json={"name": "性能测试空间", "description": "用于性能测试"},
        ) as resp:
            if resp.status == 201:
                result = await resp.json()
                self.space_id = result["id"]

    async def measure_request(
        self, method: str, url: str, **kwargs
    ) -> Dict[str, Any]:
        """测量单个请求的性能"""
        start_time = time.time()
        error = None
        status = 0

        try:
            async with self.session.request(method, url, **kwargs) as resp:
                status = resp.status
                await resp.read()  # 确保读取完整响应
        except Exception as e:
            error = str(e)

        elapsed = (time.time() - start_time) * 1000  # 转换为毫秒

        return {
            "method": method,
            "url": url,
            "status": status,
            "elapsed_ms": elapsed,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

    async def test_endpoint_performance(
        self, name: str, method: str, endpoint: str, **kwargs
    ) -> Dict[str, Any]:
        """测试单个端点的性能"""
        print(f"\n📊 测试端点: {name}")

        # 预热请求
        print("  预热中...")
        for _ in range(3):
            await self.measure_request(method, f"{API_BASE}{endpoint}", **kwargs)

        # 性能测试
        iterations = 10
        results = []
        print(f"  执行 {iterations} 次测试...")

        for i in range(iterations):
            result = await self.measure_request(
                method, f"{API_BASE}{endpoint}", **kwargs
            )
            results.append(result)
            print(f"    [{i+1}/{iterations}] {result['elapsed_ms']:.2f}ms")

        # 计算统计数据
        response_times = [r["elapsed_ms"] for r in results if not r["error"]]
        errors = [r for r in results if r["error"]]

        if response_times:
            stats = {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "iterations": iterations,
                "success_count": len(response_times),
                "error_count": len(errors),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "stdev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0,
                "p95_ms": sorted(response_times)[int(len(response_times) * 0.95) - 1],
                "p99_ms": sorted(response_times)[int(len(response_times) * 0.99) - 1] if len(response_times) > 1 else response_times[0],
            }
        else:
            stats = {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "iterations": iterations,
                "success_count": 0,
                "error_count": len(errors),
                "error": "所有请求都失败了",
            }

        self.results["endpoints"][name] = stats
        return stats

    async def test_concurrent_requests(
        self, name: str, method: str, endpoint: str, concurrency: int = 10, **kwargs
    ) -> Dict[str, Any]:
        """测试并发请求"""
        print(f"\n🔄 并发测试: {name} (并发数: {concurrency})")

        async def make_request():
            return await self.measure_request(method, f"{API_BASE}{endpoint}", **kwargs)

        # 创建并发任务
        tasks = [make_request() for _ in range(concurrency)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000

        # 分析结果
        response_times = [r["elapsed_ms"] for r in results if not r["error"]]
        errors = [r for r in results if r["error"]]

        stats = {
            "name": name,
            "concurrency": concurrency,
            "total_time_ms": total_time,
            "requests_per_second": (concurrency / total_time) * 1000,
            "success_count": len(response_times),
            "error_count": len(errors),
        }

        if response_times:
            stats.update({
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
            })

        print(f"  ✅ 完成: {stats['success_count']} 成功, {stats['error_count']} 失败")
        print(f"  ⏱️  平均响应时间: {stats.get('mean_ms', 0):.2f}ms")
        print(f"  🚀 吞吐量: {stats['requests_per_second']:.2f} req/s")

        return stats

    async def test_load_scenario(
        self, name: str, duration_seconds: int = 10, requests_per_second: int = 10
    ):
        """测试负载场景"""
        print(f"\n🏋️ 负载测试: {name}")
        print(f"  持续时间: {duration_seconds}秒")
        print(f"  目标QPS: {requests_per_second}")

        results = []
        errors = []
        start_time = time.time()
        request_count = 0

        # 计算请求间隔
        interval = 1.0 / requests_per_second

        while time.time() - start_time < duration_seconds:
            # 发送请求
            request_start = time.time()

            # 随机选择端点进行测试
            endpoints = [
                ("GET", "/spaces"),
                ("GET", "/documents"),
                ("GET", "/notes"),
                ("GET", "/chat/conversations"),
            ]
            method, endpoint = endpoints[request_count % len(endpoints)]

            result = await self.measure_request(method, f"{API_BASE}{endpoint}")
            results.append(result)

            if result["error"]:
                errors.append(result)

            request_count += 1

            # 等待到下一个请求时间
            elapsed = time.time() - request_start
            if elapsed < interval:
                await asyncio.sleep(interval - elapsed)

            # 实时进度
            if request_count % 10 == 0:
                print(f"  已发送 {request_count} 请求...")

        # 计算统计
        total_time = time.time() - start_time
        response_times = [r["elapsed_ms"] for r in results if not r["error"]]

        stats = {
            "name": name,
            "duration_seconds": duration_seconds,
            "target_qps": requests_per_second,
            "actual_qps": request_count / total_time,
            "total_requests": request_count,
            "success_count": len(response_times),
            "error_count": len(errors),
            "error_rate": len(errors) / request_count * 100,
        }

        if response_times:
            stats.update({
                "mean_ms": statistics.mean(response_times),
                "median_ms": statistics.median(response_times),
                "min_ms": min(response_times),
                "max_ms": max(response_times),
                "p95_ms": sorted(response_times)[int(len(response_times) * 0.95) - 1],
                "p99_ms": sorted(response_times)[int(len(response_times) * 0.99) - 1] if len(response_times) > 1 else response_times[0],
            })

        self.results["scenarios"][name] = stats

        print(f"\n  📊 负载测试结果:")
        print(f"    - 总请求数: {stats['total_requests']}")
        print(f"    - 成功率: {(stats['success_count']/stats['total_requests']*100):.1f}%")
        print(f"    - 实际QPS: {stats['actual_qps']:.2f}")
        print(f"    - 平均响应时间: {stats.get('mean_ms', 0):.2f}ms")
        print(f"    - P95响应时间: {stats.get('p95_ms', 0):.2f}ms")
        print(f"    - P99响应时间: {stats.get('p99_ms', 0):.2f}ms")

        return stats

    async def test_stress_scenario(self):
        """压力测试场景 - 逐步增加负载"""
        print("\n🔥 压力测试: 逐步增加负载")

        stress_levels = [
            {"qps": 10, "duration": 10},
            {"qps": 20, "duration": 10},
            {"qps": 50, "duration": 10},
            {"qps": 100, "duration": 10},
        ]

        for level in stress_levels:
            await self.test_load_scenario(
                f"压力测试 {level['qps']} QPS",
                duration_seconds=level["duration"],
                requests_per_second=level["qps"],
            )

            # 如果错误率太高，停止测试
            last_scenario = self.results["scenarios"][f"压力测试 {level['qps']} QPS"]
            if last_scenario["error_rate"] > 50:
                print(f"\n⚠️  错误率过高 ({last_scenario['error_rate']:.1f}%)，停止压力测试")
                break

            # 冷却期
            print("\n  等待5秒冷却...")
            await asyncio.sleep(5)

    async def test_complex_workflow(self):
        """测试复杂工作流程"""
        print("\n🔧 测试复杂工作流程")

        workflow_start = time.time()
        steps = []

        # 1. 创建空间
        start = time.time()
        async with self.session.post(
            f"{API_BASE}/spaces",
            json={"name": f"工作流测试空间_{int(time.time())}", "description": "测试"},
        ) as resp:
            if resp.status == 201:
                space = await resp.json()
                workflow_space_id = space["id"]
                steps.append({
                    "name": "创建空间",
                    "elapsed_ms": (time.time() - start) * 1000,
                    "success": True,
                })
            else:
                steps.append({
                    "name": "创建空间",
                    "elapsed_ms": (time.time() - start) * 1000,
                    "success": False,
                })
                return

        # 2. 创建笔记
        start = time.time()
        async with self.session.post(
            f"{API_BASE}/notes",
            json={
                "title": "性能测试笔记",
                "content": "这是一个性能测试笔记" * 100,
                "space_id": workflow_space_id,
            },
        ) as resp:
            steps.append({
                "name": "创建笔记",
                "elapsed_ms": (time.time() - start) * 1000,
                "success": resp.status == 201,
            })

        # 3. 搜索文档
        start = time.time()
        async with self.session.post(
            f"{API_BASE}/documents/search",
            json={"query": "测试", "space_id": workflow_space_id},
        ) as resp:
            steps.append({
                "name": "搜索文档",
                "elapsed_ms": (time.time() - start) * 1000,
                "success": resp.status == 200,
            })

        # 4. AI对话
        start = time.time()
        async with self.session.post(
            f"{API_BASE}/chat/completions",
            json={
                "messages": [{"role": "user", "content": "什么是性能测试？"}],
                "model": "openrouter/auto",
                "space_id": workflow_space_id,
            },
        ) as resp:
            steps.append({
                "name": "AI对话",
                "elapsed_ms": (time.time() - start) * 1000,
                "success": resp.status == 200,
            })

        # 计算总结
        total_elapsed = (time.time() - workflow_start) * 1000
        success_count = sum(1 for s in steps if s["success"])

        workflow_stats = {
            "name": "复杂工作流程",
            "total_elapsed_ms": total_elapsed,
            "steps": steps,
            "success_count": success_count,
            "total_steps": len(steps),
            "success_rate": success_count / len(steps) * 100,
        }

        self.results["scenarios"]["complex_workflow"] = workflow_stats

        print(f"\n  📊 工作流程测试结果:")
        print(f"    - 总耗时: {total_elapsed:.2f}ms")
        print(f"    - 成功率: {workflow_stats['success_rate']:.1f}%")
        for step in steps:
            status = "✅" if step["success"] else "❌"
            print(f"    - {status} {step['name']}: {step['elapsed_ms']:.2f}ms")

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 70)
        print("📊 性能测试报告")
        print("=" * 70)

        # 端点性能总结
        if self.results["endpoints"]:
            print("\n🎯 端点性能测试:")
            print(f"{'端点':<30} {'平均响应':<10} {'P95':<10} {'P99':<10} {'成功率'}")
            print("-" * 70)

            for name, stats in self.results["endpoints"].items():
                if "mean_ms" in stats:
                    success_rate = stats["success_count"] / stats["iterations"] * 100
                    print(
                        f"{name:<30} "
                        f"{stats['mean_ms']:<10.2f} "
                        f"{stats['p95_ms']:<10.2f} "
                        f"{stats['p99_ms']:<10.2f} "
                        f"{success_rate:.1f}%"
                    )

        # 场景测试总结
        if self.results["scenarios"]:
            print("\n🏋️ 场景测试结果:")
            for name, stats in self.results["scenarios"].items():
                print(f"\n  {name}:")
                for key, value in stats.items():
                    if key != "name" and not key.startswith("_"):
                        if isinstance(value, float):
                            print(f"    - {key}: {value:.2f}")
                        else:
                            print(f"    - {key}: {value}")

        # 保存JSON报告
        report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 详细报告已保存: {report_file}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("\n🚀 开始性能测试套件")
        print("=" * 70)

        # 1. 基础端点性能测试
        print("\n📌 阶段1: 基础端点性能测试")
        await self.test_endpoint_performance("获取空间列表", "GET", "/spaces")
        await self.test_endpoint_performance("获取文档列表", "GET", "/documents")
        await self.test_endpoint_performance("获取笔记列表", "GET", "/notes")
        await self.test_endpoint_performance("获取对话列表", "GET", "/chat/conversations")

        # 2. 并发测试
        print("\n📌 阶段2: 并发测试")
        await self.test_concurrent_requests("并发获取空间", "GET", "/spaces", concurrency=20)
        await self.test_concurrent_requests("并发搜索文档", "POST", "/documents/search",
                                          concurrency=10, json={"query": "test"})

        # 3. 负载测试
        print("\n📌 阶段3: 负载测试")
        await self.test_load_scenario("常规负载", duration_seconds=30, requests_per_second=20)

        # 4. 压力测试
        print("\n📌 阶段4: 压力测试")
        await self.test_stress_scenario()

        # 5. 复杂工作流程
        print("\n📌 阶段5: 复杂工作流程测试")
        await self.test_complex_workflow()

        # 生成报告
        self.generate_report()


async def main():
    """主函数"""
    async with PerformanceTestSuite() as suite:
        await suite.run_all_tests()


if __name__ == "__main__":
    print("🏁 SecondBrain API 性能测试套件")
    print("⏰ 开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🔗 目标服务器:", BASE_URL)
    print("=" * 70)

    asyncio.run(main())

    print("\n✅ 性能测试完成！")