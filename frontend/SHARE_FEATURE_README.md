# 项目分享功能说明

## 功能概述

本项目已成功实现了文档分享功能，允许用户设置项目的共享权限和访问级别。

## 主要功能

### 1. 分享状态显示
- **项目页面**: 在项目标题旁边显示分享按钮，点击可打开分享设置
- **左侧边栏**: 在项目列表中显示分享状态图标
  - 🔒 私有项目（默认）
  - 👥 组织内共享
  - 🌐 公开项目
  - 📤 特定用户共享

### 2. 分享权限设置
- **Owner（所有者）**: 仅项目所有者可访问
- **Organization（组织）**: 组织内所有成员可访问
- **Public（公开）**: 组织外人员也可访问

### 3. 用户权限管理
- **Read Only（仅读）**: 用户只能查看项目内容
- **Can Edit（可编辑）**: 用户可以编辑项目内容

## 使用方法

### 设置项目分享
1. 进入任意项目页面
2. 点击项目标题旁边的分享按钮（📤图标）
3. 在分享对话框中设置：
   - 选择分享级别（Owner/Organization/Public）
   - 添加用户邮箱地址
   - 设置用户权限（Read Only/Can Edit）
4. 点击"Save"保存设置

### 查看分享状态
- **项目页面**: 分享按钮会根据当前分享状态显示不同图标
- **左侧边栏**: 项目名称右侧会显示分享状态图标

## 技术实现

### 数据结构
```javascript
sharing: {
  isShared: boolean,        // 是否已分享
  shareLevel: string,       // 'owner' | 'organization' | 'public'
  sharedWith: array,        // 分享给的用户列表
  permissions: string,      // 'read' | 'edit'
  sharedAt: string,        // 分享时间
  sharedBy: string         // 分享者ID
}
```

### 组件文件
- `src/components/modals/ShareProjectModal.js` - 分享设置模态框
- `src/components/modals/ShareProjectModal.module.css` - 分享模态框样式
- `src/contexts/ProjectContext.js` - 项目数据管理（已更新）
- `src/pages/ProjectPage.js` - 项目页面（已更新）
- `src/components/layout/LeftSidebar.js` - 左侧边栏（已更新）

### 样式特点
- 与现有UI风格保持一致
- 响应式设计
- 清晰的视觉反馈
- 直观的图标表示

## 功能特点

1. **直观的视觉反馈**: 不同分享状态用不同图标表示
2. **灵活的权限控制**: 支持多种分享级别和用户权限
3. **用户友好的界面**: 简洁的对话框设计
4. **实时状态更新**: 分享状态实时反映在界面上
5. **数据持久化**: 分享设置保存在本地存储中

## 注意事项

- 当前实现为前端演示版本
- 用户邮箱验证为基本格式检查
- 分享功能需要配合后端API实现完整的用户管理
- 建议在生产环境中添加更严格的权限验证 