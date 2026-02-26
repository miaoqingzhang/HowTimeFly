package com.howtimefly.tv.api

import com.howtimefly.tv.ServerConfig
import com.howtimefly.tv.model.*
import retrofit2.Response
import retrofit2.http.*

/**
 * HowTimeFly 后端 API 接口
 */
interface ApiService {

    // ========== 统计信息 ==========
    @GET("stats")
    suspend fun getStats(): Response<StatsResponse>

    // ========== 媒体列表 ==========
    @GET("media/timeline")
    suspend fun getTimeline(
        @Query("start_time") startTime: Long? = null,
        @Query("end_time") endTime: Long? = null,
        @Query("file_type") fileType: String? = null,
        @Query("sort") sort: String = "desc",
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): Response<TimelineResponse>

    @GET("media/pending")
    suspend fun getPendingMedia(
        @Query("limit") limit: Int = 100,
        @Query("offset") offset: Int = 0
    ): Response<TimelineResponse>

    @GET("media/{id}")
    suspend fun getMedia(@Path("id") mediaId: Int): Response<MediaItem>

    // ========== 扫描 ==========
    @POST("scan/start")
    suspend fun startScan(
        @Body request: ScanStartRequest = ScanStartRequest()
    ): Response<ScanStatusResponse>

    @GET("scan/status")
    suspend fun getScanStatus(): Response<ScanStatusResponse>

    // ========== 日期编辑 ==========
    @PUT("media/{id}/date")
    suspend fun updateMediaDate(
        @Path("id") mediaId: Int,
        @Body request: UpdateDateRequest
    ): Response<UpdateDateResponse>

    @PUT("media/batch-date")
    suspend fun batchUpdateDate(
        @Body request: BatchUpdateDateRequest
    ): Response<BatchUpdateDateResponse>
}

/**
 * API 请求/响应模型
 */

data class StatsResponse(
    val total_photos: Int,
    val total_videos: Int,
    val total_size_mb: Double,
    val date_range: DateRange?,
    val last_scan_time: Long?
)

data class DateRange(
    val earliest: Long,
    val latest: Long
)

data class TimelineResponse(
    val items: List<MediaItem>,
    val total: Int,
    val has_more: Boolean
)

data class MediaItem(
    val id: Int,
    val file_name: String,
    val file_type: String,  // "photo" or "video"
    val create_time: Long,
    val width: Int?,
    val height: Int?,
    val duration: Double?,  // 视频时长（秒）
    val thumbnail_url: String?,
    val file_url: String
)

data class ScanStartRequest(
    val paths: List<String>? = null,
    val recursive: Boolean = true
)

data class ScanStatusResponse(
    val is_running: Boolean,
    val current_scan_id: Int?,
    val status: String,
    val progress: Progress?
)

data class Progress(
    val total: Int,
    val processed: Int,
    val added: Int?,
    val updated: Int?
)

data class UpdateDateRequest(
    val create_time: Long
)

data class UpdateDateResponse(
    val id: Int,
    val file_name: String,
    val create_time: Long,
    val create_date: String
)

data class BatchUpdateDateRequest(
    val item_ids: List<Int>,
    val create_time: Long
)

data class BatchUpdateDateResponse(
    val updated_count: Int,
    val create_date: String
)
