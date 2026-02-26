# Docker Hub 自动部署指南

## 一、准备 Docker Hub 账号

### 1. 注册 Docker Hub
访问：https://hub.docker.com/

### 2. 创建 Access Token
```
登录 Docker Hub
→ Account Settings
→ Security
→ New Access Token
→ Description: GitHub Actions
→ Access permissions: Read & Write
→ Generate
→ 复制 Token（只显示一次！）
```

---

## 二、配置 GitHub Secrets

### 1. 在 GitHub 添加 Secrets

打开 GitHub 仓库：
```
https://github.com/你的用户名/how-time-fly
```

进入：
```
Settings → Secrets and variables → Actions → New repository secret
```

添加两个 Secret：

| Secret 名称 | 值 |
|-------------|---|
| `DOCKERHUB_USERNAME` | 你的 Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | 刚才创建的 Access Token |

### 2. 修改 docker-release.yml

编辑 `.github/workflows/docker-release.yml`，修改第10行：

```yaml
env:
  # 改成你的 Docker Hub 用户名
  DOCKER_IMAGE: 你的用户名/howtimefly
```

---

## 三、推送代码到 GitHub

### 添加 GitHub 远程仓库
```bash
cd D:\ZProject\HowTimeFly

# 添加 GitHub 远程
git remote add github https://github.com/你的用户名/how-time-fly.git

# 推送代码
git push github main
```

### 打标签触发构建
```bash
# 创建版本标签
git tag v1.0.0

# 推送标签
git push github v1.0.0
```

---

## 四、查看构建状态

### GitHub Actions 页面
```
https://github.com/你的用户名/how-time-fly/actions
```

构建时间：约 10-15 分钟（首次较慢）

---

## 五、在飞牛OS上使用

构建成功后，在飞牛OS SSH 中执行：

```bash
# 拉取镜像
docker pull 你的用户名/howtimefly:latest

# 或指定版本
docker pull 你的用户名/howtimefly:v1.0.0

# 启动容器
docker run -d \
  --name howtimefly \
  --restart unless-stopped \
  -p 8080:8080 \
  -e SCAN_PATHS=/volume1/photo \
  -v $(pwd)/data:/app/data \
  -v /volume1/photo:/media:ro \
  你的用户名/howtimefly:latest
```

---

## 六、支持的架构

构建的镜像支持：
- ✅ linux/amd64 (x86_64，Intel/AMD 处理器)
- ✅ linux/arm64 (ARM64，树莓派4等)

自动检测并构建多架构镜像。

---

## 七、常见问题

### Q: 构建失败怎么办？
A: 检查 GitHub Actions 日志，确认 Secrets 是否正确配置

### Q: 如何更新镜像？
A:
```bash
# 修改代码后，打新标签
git tag v1.0.1
git push github v1.0.1
```

### Q: 如何在飞牛OS上查看日志？
A:
```bash
docker logs howtimefly
docker logs -f howtimefly  # 实时查看
```

---

## 八、镜像地址示例

构建成功后，镜像地址为：
```
docker pull 你的用户名/howtimefly:latest
```

Docker Hub 页面：
```
https://hub.docker.com/r/你的用户名/howtimefly
```
