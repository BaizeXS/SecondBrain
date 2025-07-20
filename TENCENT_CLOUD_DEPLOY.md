# 🚀 腾讯云轻量服务器部署指南（30分钟）

## 第一步：购买服务器（5分钟）

### 1. 访问腾讯云
- 链接：https://cloud.tencent.com/product/lighthouse
- 新用户优惠：首月仅需 **1元**

### 2. 选择配置
- **地域**：选择离你最近的
- **镜像**：Ubuntu 22.04 LTS
- **套餐**：2核2G（足够用）
- **购买时长**：1个月

### 3. 设置登录方式
- 选择"密码"方式（更简单）
- 记住你的密码

## 第二步：部署项目（20分钟）

### 1. 登录服务器
```bash
# Windows 用户使用 PowerShell 或 CMD
# Mac/Linux 用户使用终端
ssh root@你的服务器IP
```

### 2. 一键部署（最简单）
```bash
# 方式一：直接运行
wget https://raw.githubusercontent.com/你的用户名/SecondBrain/main/tencent-deploy.sh
bash tencent-deploy.sh

# 方式二：复制粘贴
curl -o deploy.sh https://raw.githubusercontent.com/你的用户名/SecondBrain/main/tencent-deploy.sh && bash deploy.sh
```

### 3. 按提示操作
- 输入你的 GitHub 用户名
- 输入 OpenRouter API Key
- 等待自动部署

## 第三步：访问测试（5分钟）

部署完成后会显示：
```
📱 访问地址：
   前端: http://服务器IP:3000
   
👤 测试账号：
   邮箱: demo@example.com
   密码: Demo123!
```

## 🎯 快速命令（复制即用）

如果你想最快部署，登录服务器后直接复制粘贴：

```bash
# 超级一键部署（替换你的信息）
apt update && \
apt install -y docker.io docker-compose git && \
git clone https://github.com/你的GitHub用户名/SecondBrain.git && \
cd SecondBrain && \
echo "OPENROUTER_API_KEY=你的API_KEY" > backend/.env && \
docker-compose up -d && \
sleep 30 && \
docker-compose exec backend alembic upgrade head && \
echo "✅ 部署完成！访问 http://$(curl -s ifconfig.me):3000"
```

## 💡 获取 API Key

### OpenRouter（推荐）
1. 访问：https://openrouter.ai
2. 注册账号
3. 获得免费额度 $1
4. 创建 API Key

## 🔧 常用操作

### 查看日志
```bash
cd SecondBrain
docker-compose logs -f
```

### 重启服务
```bash
docker-compose restart
```

### 更新代码
```bash
git pull
docker-compose restart
```

## ❓ 常见问题

### 1. 端口访问不了？
腾讯云需要在控制台开放端口：
- 登录腾讯云控制台
- 找到你的轻量服务器
- 防火墙 → 添加规则
- 开放端口：3000, 8000

### 2. 服务启动失败？
```bash
# 查看错误日志
docker-compose logs backend
```

### 3. 需要 HTTPS？
可以使用 Cloudflare 免费 CDN

## 📱 演示准备

1. **测试所有功能**
   - 登录系统
   - AI 对话
   - 文件上传
   - 深度研究

2. **准备演示数据**
   - 上传几个 PDF
   - 创建示例对话
   - 准备测试问题

---

**祝你演示成功！** 🎉 

有问题随时查看服务器上的 `deployment-info.txt` 文件。