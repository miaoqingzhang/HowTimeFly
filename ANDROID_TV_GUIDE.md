# HowTimeFly Android TV - Android Studio 开发指南

## 一、安装 Android Studio

### 1. 下载
```
官网：https://developer.android.com/studio
大小：约 1GB
推荐版本：Hedgehog (2023.1.1) 或更高
```

### 2. 安装时选择的组件
- [x] Android SDK
- [x] Android SDK Platform-Tools
- [x] Android Virtual Device (推荐用于 TV 模拟器)
- [x] Intel x86 Emulator Accelerator (HAXM installer)

### 3. 首次启动配置
```
1. Welcome → Configure → SDK Manager
2. SDK Platforms: 勾选 Android 10.0 (Q) - Android 14
3. SDK Tools: 确保以下已安装：
   - Android SDK Build-Tools
   - Android Emulator
   - Android SDK Platform-Tools
```

---

## 二、打开项目

### 1. 打开项目
```
File → Open → 选择 android-tv 目录
```

### 2. 等待 Gradle 同步
首次打开会自动下载依赖，需要等待 5-15 分钟（取决于网络）

---

## 三、创建 Android TV 模拟器

### 1. 打开设备管理器
```
Tools → Device Manager → Create Device
```

### 2. 选择 TV 设备
```
Category: TV
选择：Television (1080p) 或 Android TV
```

### 3. 选择系统镜像
```
推荐：API 30 (R) 或更高
如果需要下载，点击 Download
```

### 4. 完成创建
```
配置虚拟机名称，点击 Finish
```

---

## 四、配置后端服务

### 方式1: 本地运行后端

```bash
# 在 D:\ZProject\HowTimeFly 目录
python run.py

# 确保监听 0.0.0.0
# 编辑 config.yaml:
# server:
#   host: "0.0.0.0"
```

### 方式2: Docker 运行

```bash
docker-compose up -d
```

### 获取服务器 IP

```bash
# Windows
ipconfig
# 找到 IPv4 地址，如 192.168.1.100
```

---

## 五、运行应用

### 1. 连接模拟器
```
点击工具栏的运行按钮 ▶️
选择刚创建的 TV 模拟器
```

### 2. 首次启动配置
```
应用会自动跳转到设置页面
输入服务器地址，如：
http://192.168.1.100:8080
点击"测试连接"
成功后返回主界面
```

---

## 六、调试技巧

### 查看日志
```
View → Tool Windows → Logcat
过滤: HowTimeFly
```

### 断点调试
```
在代码行号左侧点击设置断点
右键 Run → Debug 'app'
```

### 热重载（代码修改）
```
修改简单代码后：Ctrl+F9 (Build → Reload)
修改资源文件后自动刷新
```

---

## 七、常见问题

### Q: Gradle 同步失败
```
A: File → Invalidate Caches → Invalidate and Restart
```

### Q: 模拟器无法启动
```
A: 检查 BIOS 是否开启虚拟化 (VT-x/AMD-V)
```

### Q: 无法连接后端
```
A: 确认后端监听 0.0.0.0，且防火墙允许 8080 端口
```

### Q: 卡片图片不显示
```
A: 检查后端缩略图是否生成，查看 Logcat 错误信息
```

---

## 八、项目结构说明

```
android-tv/
├── app/src/main/
│   ├── java/com/howtimefly/tv/
│   │   ├── MainActivity.kt       # 应用入口
│   │   ├── ServerConfig.kt       # 服务器配置
│   │   ├── api/                   # 网络层
│   │   │   ├── ApiService.kt      # API 接口定义
│   │   │   └── RetrofitClient.kt  # HTTP 客户端
│   │   ├── browse/                # 浏览界面
│   │   │   ├── BrowseFragment.kt  # 主浏览界面
│   │   │   └── CardPresenter.kt   # 卡片渲染器
│   │   ├── playback/              # 播放界面
│   │   │   └── PlaybackActivity.kt
│   │   └── settings/              # 设置界面
│   │       └── SettingsActivity.kt
│   └── res/                       # 资源文件
│       ├── layout/                # 布局文件
│       ├── values/                # 字符串、颜色等
│       └── drawable/              # 图片资源
└── app/build.gradle.kts           # 依赖配置
```

---

## 九、下一步开发建议

1. **完善浏览功能**
   - 日期分组显示
   - 分页加载更多
   - 搜索功能

2. **优化播放体验**
   - 自动播放时间线
   - 播放列表管理
   - 背景音乐

3. **添加设置选项**
   - 扫描路径配置
   - 缩略图质量设置
   - 界面主题切换

4. **性能优化**
   - 图片缓存策略
   - 预加载机制
   - 内存优化

---

有任何问题欢迎提问！
