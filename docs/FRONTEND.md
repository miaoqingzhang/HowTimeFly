# HowTimeFly 前端设计

## 页面结构

### 主界面布局

```
┌─────────────────────────────────────────────────────────┐
│  Header: HowTimeFly                    [设置] [扫描] [?] │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐  ┌──────────────────────────────────┐  │
│  │             │  │   时间线内容区                     │  │
│  │   侧边栏     │  │                                   │  │
│  │             │  │   ┌─────────────────────────┐    │  │
│  │ • 全部媒体   │  │   │  2024年1月              │    │  │
│  │   □ 照片     │  │   │  ┌───┐ ┌───┐ ┌───┐      │    │  │
│  │   □ 视频     │  │   │  │   │ │   │ │   │      │    │  │
│  │             │  │   │  └───┘ └───┘ └───┘      │    │  │
│  │ • 播放列表   │  │   │  2024年1月              │    │  │
│  │   □ 我的回忆 │  │   │  ┌─────────────┐       │    │  │
│  │   □ 旅行     │  │   │  │  ▶ 视频缩略  │       │    │  │
│  │             │  │   │  └─────────────┘       │    │  │
│  │ • 时间筛选   │  │   │  2023年12月             │    │  │
│  │   □ 最近一周 │  │   │  ┌───┐ ┌───┐ ┌───┐      │    │  │
│  │   □ 最近一月 │  │   │  │   │ │   │ │   │      │    │  │
│  │   □ 全部     │  │   │  └───┘ └───┘ └───┘      │    │  │
│  │             │  │   │                         │    │  │
│  │             │  │   │  [加载更多...]          │    │  │
│  │             │  │   └─────────────────────────┘    │  │
│  └─────────────┘  └──────────────────────────────────┘  │
│                                                           │
│  Footer: 扫描状态: 就绪 | 媒体数: 12,345 | 最后更新: 5分钟前 │
└─────────────────────────────────────────────────────────┘
```

### 播放模式布局

```
┌─────────────────────────────────────────────────────────┐
│  [×] 退出播放              [❚❚] 暂停    [⊲] 上一张  [⊳] 下一张 │
├─────────────────────────────────────────────────────────┤
│                                                           │
│                                                           │
│                                                           │
│                    ┌─────────────────┐                   │
│                    │                 │                   │
│                    │                 │                   │
│                    │    当前媒体      │                   │
│                    │                 │                   │
│                    │                 │                   │
│                    └─────────────────┘                   │
│                                                           │
│                                                           │
│          2024-01-15 14:30    自动人像模式                │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 核心交互流程

### 1. 首页加载流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 打开页面 │ -> │ 加载配置 │ -> │ 请求统计 │ -> │ 渲染界面 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                     │
                     ▼
              ┌─────────────┐
              │ 显示加载动画 │
              └─────────────┘
                     │
                     ▼
              ┌─────────────────┐
              │ 首屏API请求     │
              │ - /api/v1/stats │
              │ - /api/v1/media│
              │   ?limit=50    │
              └─────────────────┘
                     │
                     ▼
              ┌─────────────────┐
              │ 渲染时间线       │
              │ - 虚拟滚动       │
              │ - 图片懒加载     │
              └─────────────────┘
```

### 2. 点击媒体查看

```
点击缩略图
    │
    ├─ 照片: 打开模态框显示大图
    │         └─ 支持缩放、旋转
    │
    └─ 视频: 打开播放器
              └─ 检测HLS支持
                 ├─ 支持: 使用HLS.js
                 └─ 不支持: 原生video标签
```

### 3. 幻灯片播放

```
[▶ 播放按钮] 点击
    │
    ├─ 全屏显示
    ├─ 自动切换(可配置间隔)
    ├─ 键盘控制(左右箭头)
    └─ ESC退出
```

---

## 兼容性设计

### CSS变量 + 渐进增强

```css
/* 基础样式 - 兼容所有浏览器 */
.timeline-grid {
  display: block;
}

/* 现代浏览器增强 */
@supports (display: grid) {
  .timeline-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
  }
}

/* 老浏览器flexbox回退 */
@supports (display: flex) and (not (display: grid)) {
  .timeline-grid {
    display: flex;
    flex-wrap: wrap;
  }
  .timeline-item {
    flex: 0 0 200px;
    margin: 5px;
  }
}
```

### JavaScript特性检测

```javascript
// 检测工具
const supports = {
  template: 'content' in document.createElement('template'),
  picture: !!window.HTMLPictureElement,
  intersection: !!window.IntersectionObserver,
  fetch: !!window.fetch,
  webp: document.createElement('picture').canUseWebP
};

// 根据能力降级
class ImageLoader {
  constructor() {
    if (supports.intersection) {
      this.observer = new IntersectionObserver(this.onIntersect);
    }
  }

  loadImage(img) {
    if (supports.intersection) {
      this.observer.observe(img);
    } else {
      // 降级: 直接加载
      img.src = img.dataset.src;
    }
  }
}
```

---

## 组件设计

### 1. TimelineItem (时间线项)

```javascript
class TimelineItem {
  constructor(media) {
    this.media = media;
    this.element = this.render();
  }

  render() {
    const div = document.createElement('div');
    div.className = 'timeline-item';
    div.innerHTML = `
      <div class="thumbnail-container">
        <img data-src="${this.media.thumbnail_url}"
             alt="${this.media.file_name}"
             class="lazy-image">
        ${this.media.type === 'video' ? '<span class="video-badge">▶</span>' : ''}
      </div>
      <div class="item-info">
        <span class="item-date">${this.formatDate(this.media.create_time)}</span>
      </div>
    `;
    return div;
  }

  formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN');
  }
}
```

### 2. MediaViewer (媒体查看器)

```javascript
class MediaViewer {
  constructor() {
    this.container = document.getElementById('viewer');
    this.currentIndex = 0;
    this.mediaList = [];
    this.isFullscreen = false;
  }

  open(media, allMedia) {
    this.mediaList = allMedia;
    this.currentIndex = allMedia.findIndex(m => m.id === media.id);
    this.show();
    this.enterFullscreen();
  }

  show() {
    const media = this.mediaList[this.currentIndex];
    if (media.type === 'video') {
      this.showVideo(media);
    } else {
      this.showPhoto(media);
    }
  }

  showVideo(media) {
    // 检测HLS支持
    if (Hls.isSupported() && media.hls_url) {
      this.playHLS(media.hls_url);
    } else {
      this.playNative(media.url);
    }
  }

  next() {
    if (this.currentIndex < this.mediaList.length - 1) {
      this.currentIndex++;
      this.show();
    }
  }

  prev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.show();
    }
  }
}
```

### 3. Slideshow (幻灯片)

```javascript
class Slideshow {
  constructor(viewer) {
    this.viewer = viewer;
    this.interval = 5000; // 默认5秒
    this.timer = null;
    this.isActive = false;
  }

  start() {
    this.isActive = true;
    this.scheduleNext();
  }

  scheduleNext() {
    this.timer = setTimeout(() => {
      if (this.isActive) {
        this.viewer.next();
        this.scheduleNext();
      }
    }, this.interval);
  }

  stop() {
    this.isActive = false;
    clearTimeout(this.timer);
  }

  setInterval(seconds) {
    this.interval = seconds * 1000;
    if (this.isActive) {
      this.stop();
      this.start();
    }
  }
}
```

---

## API调用示例

```javascript
class ApiClient {
  constructor(baseUrl = '/api/v1') {
    this.baseUrl = baseUrl;
  }

  async getStats() {
    const res = await fetch(`${this.baseUrl}/stats`);
    return res.json();
  }

  async getTimeline(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${this.baseUrl}/media/timeline?${query}`);
    return res.json();
  }

  async getMedia(id) {
    const res = await fetch(`${this.baseUrl}/media/${id}`);
    return res.json();
  }

  async startScan(paths) {
    const res = await fetch(`${this.baseUrl}/scan/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paths })
    });
    return res.json();
  }

  // 获取缩略图URL
  getThumbnailUrl(mediaId, size = 'medium') {
    return `${this.baseUrl}/media/${mediaId}/thumbnail?size=${size}`;
  }

  // 获取媒体文件URL
  getMediaUrl(mediaId) {
    return `${this.baseUrl}/media/${mediaId}/file`;
  }
}
```

---

## 响应式断点

```css
/* 超小屏幕 (老式电视盒子) */
@media (max-width: 600px) {
  .timeline-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .sidebar {
    display: none;  /* 隐藏侧边栏，使用顶部菜单 */
  }
}

/* 小屏幕 (720p电视) */
@media (min-width: 601px) and (max-width: 1280px) {
  .timeline-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* 大屏幕 (1080p电视) */
@media (min-width: 1281px) {
  .timeline-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

/* 4K电视 */
@media (min-width: 3840px) {
  .timeline-grid {
    grid-template-columns: repeat(8, 1fr);
  }
}
```

---

## 性能优化

### 1. 虚拟滚动

```javascript
class VirtualScroll {
  constructor(container, itemHeight, renderItem) {
    this.container = container;
    this.itemHeight = itemHeight;
    this.renderItem = renderItem;
    this.visibleItems = Math.ceil(container.clientHeight / itemHeight) + 2;
    this.startIndex = 0;

    container.addEventListener('scroll', () => this.onScroll());
  }

  onScroll() {
    const scrollTop = this.container.scrollTop;
    const newStartIndex = Math.floor(scrollTop / this.itemHeight);

    if (newStartIndex !== this.startIndex) {
      this.startIndex = newStartIndex;
      this.render();
    }
  }

  render() {
    const end = Math.min(this.startIndex + this.visibleItems, this.data.length);
    const subset = this.data.slice(this.startIndex, end);

    this.container.innerHTML = '';
    subset.forEach(item => {
      this.container.appendChild(this.renderItem(item));
    });
  }
}
```

### 2. 图片懒加载

```javascript
class LazyImage {
  constructor(img) {
    this.img = img;
    this.loaded = false;

    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            this.load();
            this.observer.disconnect();
          }
        });
      });
      this.observer.observe(img);
    } else {
      // 降级：直接加载
      this.load();
    }
  }

  load() {
    if (this.loaded) return;
    this.loaded = true;

    this.img.src = this.img.dataset.src;
    this.img.classList.add('loaded');
  }
}
```

### 3. 预加载策略

```javascript
class Preloader {
  constructor(client, preloadCount = 3) {
    this.client = client;
    this.preloadCount = preloadCount;
    this.preloaded = new Set();
  }

  preload(currentIndex, mediaList) {
    for (let i = 1; i <= this.preloadCount; i++) {
      const nextIndex = currentIndex + i;
      const prevIndex = currentIndex - i;

      if (nextIndex < mediaList.length) {
        this.loadMedia(mediaList[nextIndex]);
      }
      if (prevIndex >= 0) {
        this.loadMedia(mediaList[prevIndex]);
      }
    }
  }

  loadMedia(media) {
    if (this.preloaded.has(media.id)) return;

    const img = new Image();
    img.src = this.client.getThumbnailUrl(media.id, 'large');
    this.preloaded.add(media.id);
  }
}
```

---

## 键盘快捷键

| 按键 | 功能 |
|------|------|
| ESC | 退出全屏/关闭查看器 |
| ← | 上一张 |
| → | 下一张 |
| Space | 暂停/播放 |
| F | 全屏切换 |
| S | 开始/停止幻灯片 |
| +/- | 调整幻灯片间隔 |

---

## 电视盒子特殊处理

### 1. 遥控器支持

```javascript
// 映射遥控器按键
document.addEventListener('keydown', (e) => {
  switch(e.key) {
    case 'ArrowUp':    // 方向键上
    case 'ArrowDown':  // 方向键下
      // 滚动页面
      break;
    case 'Enter':      // 确认键
      // 相当于点击
      break;
    case 'Back':       // 返回键
      // 返回上一页
      break;
  }
});
```

### 2. 焦点管理

```css
/* 大焦点框，适合遥控器选择 */
:focus {
  outline: 3px solid #00a8ff;
  outline-offset: 2px;
}

/* 隐藏鼠标，电视没有鼠标 */
@media (hover: none) and (pointer: coarse) {
  body {
    cursor: none;
  }
}
```

### 3. 字体缩放

```css
/* 电视距离较远，需要更大的字体 */
html {
  font-size: 18px;  /* 基础字体更大 */
}

@media (min-width: 1920px) {
  html {
    font-size: 22px;  /* 4K电视更大 */
  }
}
```

---

## 调试支持

```javascript
// 开发模式控制台
if (location.search.includes('debug=1')) {
  window.__DEBUG__ = {
    api: new ApiClient(),
    timeline: null,
    viewer: null
  };

  // 暴露到控制台
  console.log('Debug mode enabled. Access via window.__DEBUG__');
}
```
