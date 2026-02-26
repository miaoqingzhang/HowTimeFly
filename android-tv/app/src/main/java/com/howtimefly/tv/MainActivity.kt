package com.howtimefly.tv

import android.content.Intent
import android.os.Bundle
import androidx.fragment.app.FragmentActivity

/**
 * HowTimeFly TV 主入口
 */
class MainActivity : FragmentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 检查是否已配置服务器
        if (ServerConfig.isConfigured(this)) {
            // 显示主界面
            setContentView(R.layout.activity_main)
        } else {
            // 跳转到设置页面
            startActivity(Intent(this, SettingsActivity::class.java))
            finish()
        }
    }
}
