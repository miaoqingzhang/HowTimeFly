# HowTimeFly Android TV

连接 HowTimeFly 后端服务的 Android TV 应用

## 功能特性

- 🖥️ Android TV Leanback 界面
- 📺 遥控器操作优化
- 🎬 视频播放（ExoPlayer）
- 📷 照片浏览
- ⏯️ 自动播放模式
- 🔗 连接后端 API 服务

## 系统要求

- Android 5.0 (API 21) 或更高版本
- 需要运行 HowTimeFly 后端服务

## 构建步骤

### 1. 使用 Android Studio

```bash
# 打开项目
android-studio android-tv/

# 点击 Build → Make Project
# 或 Build → Generate Signed APK
```

### 2. 使用命令行

```bash
cd android-tv
./gradlew assembleDebug
```

## 安装到电视盒子

### 方式1: 通过 USB

```bash
# 连接 ADB
adb connect 电视盒子IP:5555

# 安装 APK
adb install app/build/outputs/apk/debug/app-debug.apk
```

### 方式2: 通过 TV 应用商店（发布后）

## 配置

首次启动需要配置服务器地址：

1. 打开应用
2. 进入设置
3. 输入后端服务器地址（如：http://192.168.1.100:8080）
4. 点击"测试连接"确认
5. 返回主界面即可使用

## 开发

### 项目结构

```
android-tv/
├── app/
│   └── src/main/
│       ├── java/com/howtimefly/tv/
│       │   ├── api/           # API 接口
│       │   ├── browse/        # 浏览界面
│       │   ├── playback/      # 播放界面
│       │   └── settings/      # 设置界面
│       ├── res/               # 资源文件
│       └── AndroidManifest.xml
├── build.gradle.kts
└── settings.gradle.kts
```

### 依赖库

- [Leanback](https://developer.android.com/wear/leanback) - Android TV UI
- [ExoPlayer](https://github.com/google/ExoPlayer) - 视频播放
- [Retrofit](https://square.github.io/retrofit/) - API 请求
- [Glide](https://github.com/bumptech/glide) - 图片加载

## License

MIT
