# GitHub Actions 部署指南

## 一、创建 GitHub 仓库

1. 访问 https://github.com/new
2. 创建仓库 `how-time-fly`
3. **不要**初始化 README

## 二、添加 GitHub 远程仓库

```bash
# 在本地项目目录执行
git remote add github https://github.com/你的用户名/how-time-fly.git

# 推送代码
git push github main
```

## 三、配置镜像仓库权限

1. GitHub 仓库页面 → **Settings** → **Actions** → **General**
2. 滚动到底部，启用：
   - ☑️ Allow all actions and reusable workflows
   - ☑️ Read and write permissions

## 四、触发构建

```bash
# 打标签
git tag v1.0.0
git push github v1.0.0
```

构建完成后，镜像地址：
```
ghcr.io/你的用户名/how-time-fly:latest
```

## 五、在飞牛OS 上拉取使用

```bash
# 登录 GitHub 容器镜像服务
docker login ghcr.io -u 你的GitHub用户名 -p 你的GitHub个人令牌

# 个人令牌获取：GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
# 勾选 read:packages 权限

# 拉取镜像
docker pull ghcr.io/你的用户名/how-time-fly:latest

# 使用镜像
docker run -d --name howtimefly -p 8080:8080 \
  -v /你的媒体路径:/media:ro \
  ghcr.io/你的用户名/how-time-fly:latest
```

## 常见问题

### Q: 构建需要多长时间？
A: 首次约 5-10 分钟，后续使用缓存约 2-3 分钟

### Q: 支持哪些架构？
A: 默认构建 linux/amd64 和 linux/arm64，兼容 x86 和 ARM NAS

### Q: 镜像有大小限制吗？
A: GitHub Packages 公开仓库无限制

### Q: 如何查看构建进度？
A: 仓库页面 → Actions 标签 → 查看工作流运行状态
