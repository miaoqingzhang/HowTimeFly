package com.howtimefly.tv.playback

import android.net.Uri
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.google.android.exoplayer2.ExoPlayer
import com.google.android.exoplayer2.MediaItem
import com.google.android.exoplayer2.Player
import com.howtimefly.tv.R
import com.howtimefly.tv.ServerConfig
import com.howtimefly.tv.api.MediaItem
import com.howtimefly.tv.api.RetrofitClient
import com.howtimefly.tv.databinding.ActivityPlaybackBinding
import kotlinx.coroutines.launch

/**
 * 媒体播放 Activity
 */
class PlaybackActivity : AppCompatActivity() {

    private lateinit var binding: ActivityPlaybackBinding
    private var player: ExoPlayer? = null
    private var currentMediaIndex = 0
    private val mediaList = mutableListOf<MediaItem>()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        binding = ActivityPlaybackBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // 获取传入的媒体ID和列表
        val mediaId = intent.getIntExtra(EXTRA_MEDIA_ID, -1)
        val ids = intent.getIntegerArrayListExtra(EXTRA_MEDIA_LIST) ?: arrayListOf()

        if (mediaId == -1 || ids.isEmpty()) {
            finish()
            return
        }

        loadMediaList(ids, mediaId)
    }

    private fun loadMediaList(ids: ArrayList<Int>, currentId: Int) {
        lifecycleScope.launch {
            try {
                // 批量获取媒体信息
                mediaList.clear()
                ids.forEach { id ->
                    try {
                        val response = RetrofitClient.getApiService(this@PlaybackActivity).getMedia(id)
                        if (response.isSuccessful) {
                            response.body()?.let { mediaList.add(it) }
                        }
                    } catch (e: Exception) {
                        // 忽略单个媒体加载失败
                    }
                }

                // 找到当前播放索引
                currentMediaIndex = mediaList.indexOfFirst { it.id == currentId }
                if (currentMediaIndex == -1) currentMediaIndex = 0

                setupPlayer()
                playMedia(currentMediaIndex)

            } catch (e: Exception) {
                finish()
            }
        }
    }

    private fun setupPlayer() {
        player = ExoPlayer.Builder(this).build().apply {
            // 监听播放完成，自动播放下一个
            addListener(object : Player.Listener {
                override fun onPlaybackStateChanged(playbackState: Int) {
                    if (playbackState == Player.STATE_ENDED) {
                        playNext()
                    }
                }
            })
        }

        binding.playerView.player = player
    }

    private fun playMedia(index: Int) {
        if (index !in mediaList.indices) return

        currentMediaIndex = index
        val media = mediaList[index]

        when (media.file_type) {
            "video" -> {
                // 播放视频
                binding.playerView.visibility = View.VISIBLE
                binding.imageView.visibility = View.GONE

                val videoUrl = ServerConfig.getMediaUrl(this, media.file_url)
                val mediaItem = MediaItem.fromUri(Uri.parse(videoUrl))
                player?.setMediaItem(mediaItem)
                player?.prepare()
                player?.play()
            }
            "photo" -> {
                // 显示照片
                binding.playerView.visibility = View.GONE
                binding.imageView.visibility = View.VISIBLE

                val imageUrl = ServerConfig.getMediaUrl(this, media.file_url)
                com.bumptech.glide.Glide.with(this)
                    .load(imageUrl)
                    .fitCenter()
                    .into(binding.imageView)

                // 照片自动播放模式（如果启用）
                if (isAutoPlayEnabled()) {
                    startPhotoTimer()
                }
            }
        }

        updateInfo()
    }

    private fun playNext() {
        if (currentMediaIndex < mediaList.size - 1) {
            playMedia(currentMediaIndex + 1)
        } else {
            // 播放完毕
            finish()
        }
    }

    private fun playPrevious() {
        if (currentMediaIndex > 0) {
            playMedia(currentMediaIndex - 1)
        }
    }

    private fun updateInfo() {
        val media = mediaList[currentMediaIndex]
        binding.titleText.text = media.file_name
        binding.indexText.text = "${currentMediaIndex + 1} / ${mediaList.size}"
    }

    private fun isAutoPlayEnabled(): Boolean {
        // 从设置中读取
        return getSharedPreferences("settings", MODE_PRIVATE)
            .getBoolean("auto_play", false)
    }

    private fun startPhotoTimer() {
        // TODO: 实现照片自动播放计时器
    }

    override fun onPause() {
        super.onPause()
        player?.pause()
    }

    override fun onDestroy() {
        super.onDestroy()
        player?.release()
        player = null
    }

    companion object {
        const val EXTRA_MEDIA_ID = "media_id"
        const val EXTRA_MEDIA_LIST = "media_list"
    }
}
