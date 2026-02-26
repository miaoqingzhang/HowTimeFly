# HowTimeFly Docker 部署指南

适用于飞牛OS (FNOS) 和其他支持 Docker 的 NAS 系统

---

## 一、使用 Gitee Go 构建镜像

### 1. 推送代码到 Gitee

```bash
# 在 Gitee 创建仓库后，推送代码
git remote add gitee https://gitee.com/你的用户名/howtimefly.git
git push -u gitee main
```

### 2. 在 Gitee 启用 Gitee Go

1. 进入 Gitee 仓库页面
2. 点击 "服务" → "Gitee Go"
3. 启用 CI/CD 功能
4. 代码推送后会自动构建

### 3. 导出镜像（本地无 Docker 时）

如果 Gitee Go 构建成功，下载构建的 `.tar` 镜像文件，然后：

```bash
# 在 NAS 上加载镜像
docker load -i howtimefly-latest.tar
```

---

## 二、在飞牛OS 上部署

### 方式1: 使用 docker-compose（推荐）

1. **编辑配置文件**

```bash
# 创建部署目录
mkdir -p ~/howtimefly
cd ~/howtimefly

# 复制 docker-compose.nas.yml 为 docker-compose.yml
cp docker-compose.nas.yml docker-compose.yml
```

2. **修改扫描路径**

编辑 `docker-compose.yml`，修改以下部分：

```yaml
environment:
  # 单个目录
  - SCAN_PATHS=/volume1/photo

  # 多个目录（冒号分隔）
  - SCAN_PATHS=/volume1/photo:/volume1/video:/volume2/backup

volumes:
  # 重要：挂载路径必须与 SCAN_PATHS 对应
  - /volume1/photo:/media:ro
```

3. **启动容器**

```bash
docker-compose up -d
```

### 方式2: 使用 docker run 命令

```bash
docker run -d \
  --name howtimefly \
  --restart unless-stopped \
  -p 8080:8080 \
  -e SCAN_PATHS=/volume1/photo:/volume1/video \
  -e SCAN_RECURSIVE=true \
  -e TZ=Asia/Shanghai \
  -v $(pwd)/data:/app/data \
  -v /volume1/photo:/media/photo:ro \
  -v /volume1/video:/media/video:ro \
  howtimefly:latest
```

---

## 三、环境变量配置说明

| 环境变量 | 说明 | 示例 | 默认值 |
|---------|------|------|--------|
| `SCAN_PATHS` | 扫描路径（多个用冒号分隔） | `/media/photos:/media/videos` | `/media` |
| `SCAN_RECURSIVE` | 是否递归扫描 | `true` 或 `false` | `true` |
| `TZ` | 时区 | `Asia/Shanghai` | `UTC` |

---

## 四、常见 NAS 路径配置

### 飞牛OS (FNOS)
```yaml
- SCAN_PATHS=/vol1/1000/共享文件夹/photo:/vol1/1000/共享文件夹/video
volumes:
  - /vol1/1000/共享文件夹/photo:/media/photo:ro
```

### 群晖 (Synology)
```yaml
- SCAN_PATHS=/volume1/photo:/volume2/video
volumes:
  - /volume1/photo:/media/photo:ro
  - /volume2/video:/media/video:ro
```

### 威联通 (QNAP)
```yaml
- SCAN_PATHS=/share/CACHEDEV1_DATA/Photos
volumes:
  - /share/CACHEDEV1_DATA/Photos:/media:ro
```

---

## 五、验证部署

1. **访问服务**
   - 浏览器打开: `http://NAS_IP:8080`
   - API 文档: `http://NAS_IP:8080/docs`

2. **查看日志**
   ```bash
   docker logs howtimefly
   ```

3. **启动扫描**
   - 点击页面上的 "扫描" 按钮
   - 或调用 API: `POST /api/v1/scan/start`

---

## 六、故障排查

### 问题：扫描不到文件
```bash
# 检查容器内路径是否正确
docker exec -it howtimefly ls -la /media

# 查看当前配置
docker exec -it howtimefly cat /app/config.yaml
```

### 问题：无法访问前端
```bash
# 检查容器状态
docker ps | grep howtimefly

# 检查端口
docker port howtimefly
```

---

## 七、手动构建镜像（本地有 Docker 时）

```bash
# 构建镜像
docker build -t howtimefly:latest .

# 导出镜像（用于传输到 NAS）
docker save howtimefly:latest -o howtimefly.tar

# 在 NAS 上加载
docker load -i howtimefly.tar
```
