package com.howtimefly.tv

import android.content.Context
import android.content.SharedPreferences

/**
 * 服务器配置管理
 */
object ServerConfig {

    private const val PREFS_NAME = "howtimefly_prefs"
    private const val KEY_SERVER_URL = "server_url"
    private const val KEY_API_KEY = "api_key"  // 预留，用于未来认证

    private fun getPrefs(context: Context): SharedPreferences {
        return context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    /**
     * 检查是否已配置服务器
     */
    fun isConfigured(context: Context): Boolean {
        return getPrefs(context).contains(KEY_SERVER_URL)
    }

    /**
     * 获取服务器地址
     */
    fun getServerUrl(context: Context): String {
        return getPrefs(context).getString(KEY_SERVER_URL, "") ?: ""
    }

    /**
     * 设置服务器地址
     */
    fun setServerUrl(context: Context, url: String) {
        // 标准化 URL（去除末尾斜杠）
        val normalizedUrl = url.trim().trimEnd('/')
        getPrefs(context).edit()
            .putString(KEY_SERVER_URL, normalizedUrl)
            .apply()
    }

    /**
     * 获取完整的 API 地址
     */
    fun getApiUrl(context: Context, path: String): String {
        val baseUrl = getServerUrl(context)
        return "$baseUrl/api/v1$path"
    }

    /**
     * 获取媒体文件完整 URL
     */
    fun getMediaUrl(context: Context, path: String): String {
        val baseUrl = getServerUrl(context)
        return "$baseUrl$path"
    }
}
