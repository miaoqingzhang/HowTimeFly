package com.howtimefly.tv.browse

import android.os.Bundle
import android.util.Log
import androidx.core.content.ContextCompat
import androidx.leanback.app.BrowseSupportFragment
import androidx.leanback.widget.*
import androidx.lifecycle.lifecycleScope
import com.howtimefly.tv.R
import com.howtimefly.tv.ServerConfig
import com.howtimefly.tv.api.RetrofitClient
import com.howtimefly.tv.api.MediaItem
import kotlinx.coroutines.launch

/**
 * 媒体浏览主界面
 * 使用 Leanback 卡片式布局
 */
class BrowseFragment : BrowseSupportFragment() {

    private val TAG = "BrowseFragment"

    private lateinit var rowsAdapter: ArrayObjectAdapter
    private lateinit var cardPresenter: CardPresenter
    private val mediaItems = mutableListOf<MediaItem>()
    private var currentOffset = 0
    private var isLoading = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setupUI()
        loadMedia()
    }

    private fun setupUI() {
        title = "HowTimeFly"
        headersState = HEADERS_ENABLED
        isHeadersTransitionOnBackEnabled = true

        // 设置卡片展示器
        cardPresenter = CardPresenter()

        // 创建行适配器
        rowsAdapter = ArrayObjectAdapter(ListRowPresenter())
        adapter = rowsAdapter

        // 添加侧边栏菜单
        setupRows()
    }

    private fun setupRows() {
        // 时间线
        val timelineRow = ListRow(
            HeaderItem(0, "时间线"),
            ArrayObjectAdapter(cardPresenter).apply {
                // 媒体项目将在这里动态添加
            }
        )
        rowsAdapter.add(timelineRow)

        // 待处理（如果有）
        // val pendingRow = ...
    }

    private fun loadMedia() {
        if (isLoading) return
        isLoading = true

        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val apiService = RetrofitClient.getApiService(requireContext())
                val response = apiService.getTimeline(
                    limit = 50,
                    offset = currentOffset,
                    sort = "desc"  // 最新在前
                )

                if (response.isSuccessful && response.body() != null) {
                    val timeline = response.body()!!
                    mediaItems.addAll(timeline.items)
                    currentOffset += timeline.items.size

                    updateUI(timeline.items)

                    Log.d(TAG, "加载了 ${timeline.items.size} 项，总计 ${timeline.total}")
                } else {
                    Log.e(TAG, "加载失败: ${response.code()}")
                }

            } catch (e: Exception) {
                Log.e(TAG, "网络请求失败", e)
                showError("无法连接到服务器")
            } finally {
                isLoading = false
            }
        }
    }

    private fun updateUI(items: List<MediaItem>) {
        // 获取第一行（时间线）
        val row = rowsAdapter.get(0) as? ListRow ?: return
        val rowAdapter = row.adapter as ArrayObjectAdapter

        // 添加媒体卡片
        items.forEach { media ->
            rowAdapter.add(MediaCard(media))
        }
    }

    private fun showError(message: String) {
        // 显示错误提示
    }
}

/**
 * 媒体卡片数据
 */
data class MediaCard(
    val media: MediaItem
) {
    val id: Long = media.id.toLong()
    val title: String = media.file_name
    val subtitle: String = formatDate(media.create_time)
    val imageUrl: String? = media.thumbnail_url
    val isVideo: Boolean = media.file_type == "video"

    private fun formatDate(timestamp: Long): String {
        val date = java.util.Date(timestamp * 1000)
        val sdf = java.text.SimpleDateFormat("yyyy-MM-dd HH:mm", java.util.Locale.getDefault())
        return sdf.format(date)
    }
}
