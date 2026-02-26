package com.howtimefly.tv.settings

import android.os.Bundle
import android.widget.Toast
import androidx.fragment.app.FragmentActivity
import androidx.leanback.preference.LeanbackPreferenceFragmentCompat
import androidx.leanback.preference.LeanbackSettingsFragmentCompat
import androidx.preference.EditTextPreference
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import com.howtimefly.tv.R
import com.howtimefly.tv.ServerConfig
import com.howtimefly.tv.api.RetrofitClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * 设置入口 Activity
 */
class SettingsActivity : FragmentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(android.R.id.content, SettingsFragment())
                .commit()
        }
    }

    class SettingsFragment : LeanbackSettingsFragmentCompat() {
        override fun onPreferenceStartInitialScreen() {
            startPreferenceFragment(ServerPrefsFragment())
        }

        override fun onPreferenceStartFragment(
            caller: PreferenceFragmentCompat,
            pref: Preference
        ): Boolean {
            return false
        }
    }

    class ServerPrefsFragment : LeanbackPreferenceFragmentCompat() {
        override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
            preferenceManager.preferenceDataStore = null
            setPreferencesFromResource(R.xml.preferences, rootKey)

            setupServerUrlPreference()
            setupTestConnection()
        }

        private fun setupServerUrlPreference() {
            val serverPref = findPreference<EditTextPreference>("server_url")
            serverPref?.summary = ServerConfig.getServerUrl(requireContext())

            serverPref?.setOnPreferenceChangeListener { preference, newValue ->
                val url = newValue as String
                ServerConfig.setServerUrl(requireContext(), url)
                preference.summary = url
                true
            }
        }

        private fun setupTestConnection() {
            val testPref = findPreference<Preference>("test_connection")
            testPref?.setOnPreferenceClickListener {
                testServerConnection()
                true
            }
        }

        private fun testServerConnection() {
            val context = requireContext()
            CoroutineScope(Dispatchers.Main).launch {
                try {
                    withContext(Dispatchers.IO) {
                        // 尝试初始化并调用 API
                        RetrofitClient.reinit(context)
                        val api = RetrofitClient.getApiService(context)
                        api.getStats()
                    }
                    Toast.makeText(context, "连接成功！", Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    Toast.makeText(context, "连接失败: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }
}
