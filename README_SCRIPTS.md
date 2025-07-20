# 📚 项目脚本说明

## 核心脚本（共5个）

### 1. `start.sh` - 本地启动脚本
- **用途**：本地开发环境一键启动
- **功能**：启动 Docker、初始化数据库、创建测试账号
- **使用**：`./start.sh`

### 2. `tencent-deploy.sh` - 腾讯云部署脚本
- **用途**：在腾讯云服务器上自动部署
- **功能**：安装依赖、配置环境、启动服务
- **使用**：`bash tencent-deploy.sh`

### 3. `test.sh` - 测试脚本
- **用途**：运行单元测试和集成测试
- **功能**：执行 pytest、生成测试报告
- **使用**：`./test.sh`

### 4. `create-demo.sh` - 创建演示数据
- **用途**：为毕设演示创建示例数据
- **功能**：创建用户、空间、笔记、对话等
- **使用**：`./create-demo.sh`

### 5. `create-demo-data.py` - 演示数据生成器
- **用途**：Python 脚本，定义演示数据内容
- **功能**：被 create-demo.sh 调用
- **注意**：不直接执行

## 使用流程

### 本地开发
```bash
./start.sh          # 启动项目
./create-demo.sh    # 创建演示数据（可选）
./test.sh           # 运行测试（可选）
```

### 服务器部署
```bash
# 在腾讯云服务器上
bash tencent-deploy.sh  # 自动部署
```

## 文件组织
```
SecondBrain/
├── start.sh            # 本地启动
├── tencent-deploy.sh   # 服务器部署
├── test.sh             # 运行测试
├── create-demo.sh      # 创建演示数据
└── create-demo-data.py # 演示数据定义
```