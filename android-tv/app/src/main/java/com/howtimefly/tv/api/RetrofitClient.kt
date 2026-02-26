package com.howtimefly.tv.api

import android.content.Context
import com.howtimefly.tv.ServerConfig
 okhttp3.OkHttpClient
 okhttp3.logging.HttpLoggingInterceptor
 retrofit2.Retrofit
 retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

/**
 * Retrofit 客户端单例
 */
object RetrofitClient {

    private var retrofit: Retrofit? = null
    private var apiService: ApiService? = null

    /**
     * 初始化 Retrofit 客户端
     */
    fun init(context: Context) {
        val serverUrl = ServerConfig.getServerUrl(context)
        if (serverUrl.isEmpty()) {
            throw IllegalStateException("服务器未配置")
        }

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val okHttpClient = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(loggingInterceptor)
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                    .addHeader("Accept", "application/json")
                    .build()
                chain.proceed(request)
            }
            .build()

        retrofit = Retrofit.Builder()
            .baseUrl("$serverUrl/api/v1/")
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        apiService = retrofit?.create(ApiService::class.java)
    }

    /**
     * 获取 API 服务
     */
    fun getApiService(context: Context): ApiService {
        if (apiService == null) {
            init(context)
        }
        return apiService ?: throw IllegalStateException("API 服务未初始化")
    }

    /**
     * 重新初始化（服务器地址变更时调用）
     */
    fun reinit(context: Context) {
        retrofit = null
        apiService = null
        init(context)
    }
}
