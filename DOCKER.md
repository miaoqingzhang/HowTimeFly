# HowTimeFly Docker 部署说明

## 通过环境变量动态配置扫描路径

### 方法一：使用 docker-compose.yml（推荐）

编辑 `docker-compose.yml` 文件中的 `volumes` 和 `environment` 部分：

```yaml
services:
  howtimefly:
    volumes:
      # 挂载你的媒体文件目录到容器内
      - /你的/照片/路径:/media/photos:ro
      - /你的/视频/路径:/media/videos:ro
      - /你的/下载/路径:/media/downloads:ro

    environment:
      # 配置扫描路径（使用容器内的路径，用冒号分隔）
      - SCAN_PATHS=/media/photos:/media/videos:/media/downloads

      # 是否递归扫描子目录
      - SCAN_RECURSIVE=true
```

然后启动：
```bash
docker-compose up -d
```

### 方法二：使用 docker run 命令

```bash
docker run -d \
  --name howtimefly \
  -p 8080:8080 \
  -v /你的/照片/路径:/media/photos:ro \
  -v /你的/视频/路径:/media/videos:ro \
  -e SCAN_PATHS=/media/photos:/media/videos \
  -e SCAN_RECURSIVE=true \
  howtimefly
```

### 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SCAN_PATHS` | 扫描路径（多个用冒号分隔） | `/media/photos:/media/videos` |
| `SCAN_RECURSIVE` | 是否递归扫描子目录 | `true` 或 `false` |
| `TZ` | 时区设置 | `Asia/Shanghai` |

### 注意事项

1. **路径映射**：`volumes` 中的路径是 `宿主机路径:容器路径`
2. **扫描配置**：`SCAN_PATHS` 中使用的是**容器内路径**，不是宿主机路径
3. **只读挂载**：建议使用 `:ro` 只读挂载，防止误删除

### 示例：扫描百度网盘下载目录

假设你的百度网盘下载目录在 `D:/BaiduNetdiskDownload`：

```yaml
volumes:
  - D:/BaiduNetdiskDownload:/media/baidudownload:ro

environment:
  - SCAN_PATHS=/media/baidudownload
```

或者在 Windows 上使用 docker run：
```cmd
docker run -d ^
  --name howtimefly ^
  -p 8080:8080 ^
  -v D:/BaiduNetdiskDownload:/media/baidudownload:ro ^
  -e SCAN_PATHS=/media/baidudownload ^
  howtimefly
```
