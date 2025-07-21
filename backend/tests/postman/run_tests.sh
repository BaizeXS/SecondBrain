#!/bin/bash

# SecondBrain API 自动化测试脚本
# 使用 Newman 执行 Postman Collection 测试

set -e  # 遇到错误立即退出

# 默认环境为 local
ENV="${1:-local}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports/${TIMESTAMP}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 检查环境参数
if [[ "$ENV" != "local" && "$ENV" != "server" ]]; then
    print_error "无效的环境参数: $ENV"
    echo "使用方法: $0 [local|server]"
    exit 1
fi

# 设置环境变量文件
if [ "$ENV" == "local" ]; then
    ENV_FILE="${SCRIPT_DIR}/SecondBrain_Local.postman_environment.json"
    API_BASE="http://localhost:8000/api/v1"
else
    ENV_FILE="${SCRIPT_DIR}/SecondBrain_Server.postman_environment.json"
    API_BASE="http://43.160.192.140:8000/api/v1"
fi

# 检查环境文件是否存在
if [ ! -f "$ENV_FILE" ]; then
    print_error "环境文件不存在: $ENV_FILE"
    exit 1
fi

# 检查 Newman 是否安装
if ! command -v newman &> /dev/null; then
    print_error "Newman 未安装，请先安装 Newman"
    echo "安装命令: npm install -g newman newman-reporter-htmlextra"
    exit 1
fi

# 创建报告目录
mkdir -p "$REPORT_DIR"

print_info "开始执行 SecondBrain API 测试"
print_info "环境: $ENV"
print_info "API基础URL: $API_BASE"
print_info "报告目录: $REPORT_DIR"

# 定义测试集合
COLLECTIONS=(
    "00_Quick_Test.postman_collection.json"
    "01_Auth_Basic.postman_collection.json"
    "02_Core_Features.postman_collection.json"
    "03_AI_Features.postman_collection.json"
    "04_Advanced_Features.postman_collection.json"
    "05_E2E_Complete_Flow.postman_collection.json"
)

# 初始化测试结果
TOTAL_TESTS=0
FAILED_TESTS=0
FAILED_COLLECTIONS=()

# 执行测试前的健康检查
print_info "执行健康检查..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "${API_BASE}/health" || echo "000")
if [ "$HEALTH_CHECK" != "200" ]; then
    print_error "健康检查失败，服务可能未启动 (HTTP状态码: $HEALTH_CHECK)"
    exit 1
fi
print_info "健康检查通过"

# 执行每个测试集合
for collection in "${COLLECTIONS[@]}"; do
    collection_path="${SCRIPT_DIR}/${collection}"
    
    if [ ! -f "$collection_path" ]; then
        print_warning "测试集合不存在: $collection"
        continue
    fi
    
    collection_name=$(basename "$collection" .postman_collection.json)
    print_info "执行测试集合: $collection_name"
    
    # 执行 Newman 测试
    if newman run "$collection_path" \
        -e "$ENV_FILE" \
        --reporters cli,htmlextra,junit \
        --reporter-htmlextra-export "${REPORT_DIR}/${collection_name}_report.html" \
        --reporter-junit-export "${REPORT_DIR}/${collection_name}_junit.xml" \
        --bail \
        --color on \
        --timeout-request 30000 \
        --delay-request 100; then
        
        print_info "✅ $collection_name 测试通过"
    else
        NEWMAN_EXIT_CODE=$?
        print_error "❌ $collection_name 测试失败 (退出码: $NEWMAN_EXIT_CODE)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_COLLECTIONS+=("$collection_name")
    fi
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo ""
done

# 生成汇总报告
print_info "生成测试汇总报告..."
cat > "${REPORT_DIR}/summary.txt" << EOF
SecondBrain API 测试汇总报告
========================
测试时间: $(date)
测试环境: $ENV
API基础URL: $API_BASE

测试结果:
---------
总测试集合数: $TOTAL_TESTS
通过的集合数: $((TOTAL_TESTS - FAILED_TESTS))
失败的集合数: $FAILED_TESTS

EOF

if [ ${#FAILED_COLLECTIONS[@]} -gt 0 ]; then
    echo "失败的测试集合:" >> "${REPORT_DIR}/summary.txt"
    for failed in "${FAILED_COLLECTIONS[@]}"; do
        echo "- $failed" >> "${REPORT_DIR}/summary.txt"
    done
fi

# 如果有测试失败，更新 ISSUE.md
if [ $FAILED_TESTS -gt 0 ]; then
    print_warning "发现测试失败，更新 ISSUE.md..."
    
    # 追加到 ISSUE.md
    cat >> "${SCRIPT_DIR}/ISSUE.md" << EOF

## [$(date +"%Y-%m-%d %H:%M:%S")] 自动化测试失败记录

**测试环境**: $ENV
**失败的测试集合**: ${FAILED_COLLECTIONS[@]}

### 问题摘要
- 总测试集合数: $TOTAL_TESTS
- 失败的集合数: $FAILED_TESTS

### 详细报告
请查看详细的测试报告: reports/${TIMESTAMP}/

---

EOF
fi

# 清理测试数据（可选）
# print_info "清理测试数据..."
# 这里可以调用清理API或脚本

# 显示测试结果
echo ""
print_info "======== 测试完成 ========"
print_info "测试报告已保存到: $REPORT_DIR"
print_info "总测试集合数: $TOTAL_TESTS"
if [ $FAILED_TESTS -eq 0 ]; then
    print_info "✅ 所有测试通过!"
    exit 0
else
    print_error "❌ 有 $FAILED_TESTS 个测试集合失败"
    print_error "失败的集合: ${FAILED_COLLECTIONS[@]}"
    exit 1
fi