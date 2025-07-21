# 文件上传400错误修复指南

## 🔍 问题现象

用户上传文件时出现400错误，控制台显示：
- `POST http://43.160.192.140/api/v1/documents/upload 400 (Bad Request)`
- `API Upload failed: /documents/upload`
- `Failed to upload file: README.md`

## 🎯 可能原因

400错误通常由以下原因引起：

### 1. **文件类型不支持**
- 浏览器未正确识别文件MIME类型
- `.md`文件可能被识别为空类型或`text/plain`而非`text/markdown`

### 2. **文件内容问题**
- 文件为空（0字节）
- 文件过大（超过100MB限制）
- 文件内容编码问题

### 3. **空间权限问题**
- 指定的空间不存在
- 用户没有在该空间上传文件的权限

### 4. **认证问题**
- 缺少认证token
- token过期或无效

## 🔧 诊断工具

我已经添加了详细的诊断工具来帮助定位问题：

### 使用方法

1. **点击"诊断上传"按钮**（开发环境右上角红色按钮）
2. **选择要上传的文件**
3. **查看诊断报告**

诊断工具会检查：
- ✅ 文件基本信息（名称、大小、类型）
- ✅ MIME类型兼容性
- ✅ 文件大小限制
- ✅ 空间存在和权限
- ✅ 认证状态
- ✅ 文件内容可读性

### 诊断报告示例

```
📋 文件上传诊断报告

📄 文件信息:
  名称: README.md
  大小: 3.1 KB
  类型: text/markdown

🎭 MIME类型检查:
  检测到: text/markdown
  期望: text/markdown
  支持: ✅

📏 文件大小检查:
  当前: 0.01 MB
  限制: 100 MB
  状态: ✅

🏠 空间检查:
  空间: Chat Space - 12/13/2024 (ID: 5)
  状态: ✅ 可访问

🔐 认证检查:
  Token: ✅ 存在

🎯 结论: ✅ 文件应该可以正常上传
```

## 🛠️ 修复方案

### 1. **MIME类型问题修复**

如果诊断显示MIME类型不支持，尝试：

```javascript
// 手动设置正确的MIME类型
const file = new File([originalFile], originalFile.name, {
  type: 'text/markdown'  // 强制设置为markdown类型
});
```

### 2. **空间权限问题修复**

确保文件上传到正确的空间：

```javascript
// 检查空间是否存在
try {
  const space = await apiService.space.getSpace(spaceId);
  console.log('Space verified:', space);
} catch (error) {
  console.error('Space not found:', error);
  // 创建新空间或使用其他空间
}
```

### 3. **文件大小问题修复**

检查文件大小：

```javascript
const maxSize = 100 * 1024 * 1024; // 100MB
if (file.size > maxSize) {
  throw new Error(`文件太大: ${(file.size / 1024 / 1024).toFixed(2)}MB > 100MB`);
}
if (file.size === 0) {
  throw new Error('文件为空');
}
```

### 4. **认证问题修复**

检查认证状态：

```javascript
const token = localStorage.getItem('access_token');
if (!token) {
  throw new Error('请先登录');
}
```

## 🚀 改进内容

### 1. **增强的错误日志**

现在的文件上传会显示详细的调试信息：
- 📁 FormData内容
- 📡 响应状态和头信息
- ❌ 详细的错误信息

### 2. **智能MIME类型处理**

对于`.md`文件，系统现在会：
- 检测浏览器识别的MIME类型
- 与期望的类型对比
- 提供修复建议

### 3. **完整的诊断流程**

新的诊断工具提供：
- 🔍 全面的检查项目
- 📊 详细的诊断报告
- 💡 具体的修复建议

## 📋 故障排除步骤

### 步骤1：运行诊断
1. 点击"诊断上传"按钮
2. 选择出问题的文件
3. 查看诊断报告

### 步骤2：检查控制台
查看浏览器控制台的详细日志：
```
🚀 Upload request to: http://43.160.192.140/api/v1/documents/upload
📁 FormData contents:
  space_id: 5
  file: File(name=README.md, size=3179, type=text/markdown)
  title: README.md
  tags: chat-attachment
📡 Response status: 400 Bad Request
❌ Upload error details: {detail: "不支持的文件类型: "}
```

### 步骤3：根据错误调整
根据具体错误信息：

- **"不支持的文件类型"** → 检查MIME类型
- **"空间不存在"** → 检查space_id
- **"文件为空"** → 检查文件内容
- **"文件大小超过限制"** → 检查文件大小

## 🔄 测试验证

修复后，通过以下方式验证：

1. **使用诊断工具测试**
2. **上传测试文件**（如simple.txt）
3. **查看控制台确认无错误**
4. **确认AI能读取文件内容**

## 📞 联系支持

如果问题仍然存在：

1. **保存诊断报告**
2. **截图控制台错误信息**
3. **记录文件详细信息**（名称、大小、类型）
4. **提供操作步骤**

---

**总结**：大多数400错误都是由MIME类型识别或空间权限问题引起的。使用新的诊断工具可以快速定位和解决这些问题。 