package com.sendit.app

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.graphics.Bitmap
import android.os.Build
import android.os.Bundle
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.webkit.WebSettingsCompat
import androidx.webkit.WebViewFeature
import com.google.zxing.BarcodeFormat
import com.google.zxing.qrcode.QRCodeWriter
import java.net.Inet4Address
import java.net.NetworkInterface

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var btnToggle: Button
    private lateinit var tvUrl: TextView
    private lateinit var ivQr: ImageView

    private var serverRunning = false

    // Receive updates from the foreground service
    private val serverReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                "com.sendit.SERVER_READY" -> {
                    val url = intent.getStringExtra("url") ?: return
                    onServerReady(url)
                }
                "com.sendit.SERVER_ERROR" -> {
                    val msg = intent.getStringExtra("message") ?: "Unknown error"
                    onServerError(msg)
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        btnToggle = findViewById(R.id.btnToggle)
        tvUrl = findViewById(R.id.tvUrl)
        ivQr = findViewById(R.id.ivQr)

        setupWebView()
        btnToggle.setOnClickListener { onToggleServer() }

        // Register broadcast receiver for service updates
        val filter = IntentFilter().apply {
            addAction("com.sendit.SERVER_READY")
            addAction("com.sendit.SERVER_ERROR")
        }
        ContextCompat.registerReceiver(this, serverReceiver, filter, ContextCompat.RECEIVER_NOT_EXPORTED)

        // Ask notification permission on Android 13+
        if (Build.VERSION.SDK_INT >= 33) {
            requestPermissions(arrayOf(android.Manifest.permission.POST_NOTIFICATIONS), 0)
        }
    }

    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = false
            builtInZoomControls = true
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
        }

        // Force dark theme
        if (WebViewFeature.isFeatureSupported(WebViewFeature.FORCE_DARK)) {
            WebSettingsCompat.setForceDark(webView.settings, WebSettingsCompat.FORCE_DARK_ON)
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false
            }
        }
    }

    private fun onToggleServer() {
        if (serverRunning) {
            stopServer()
        } else {
            startServer()
        }
    }

    private fun startServer() {
        val intent = Intent(this, SenditService::class.java)
        intent.action = SenditService.ACTION_START
        ContextCompat.startForegroundService(this, intent)
        btnToggle.text = getString(R.string.stop_server)
        tvUrl.text = getString(R.string.starting)
        tvUrl.visibility = android.view.View.VISIBLE
    }

    private fun stopServer() {
        val intent = Intent(this, SenditService::class.java)
        intent.action = SenditService.ACTION_STOP
        startService(intent)
        serverRunning = false
        btnToggle.text = getString(R.string.start_server)
        tvUrl.visibility = android.view.View.GONE
        ivQr.visibility = android.view.View.GONE
        webView.loadUrl("about:blank")
    }

    private fun onServerReady(url: String) {
        runOnUiThread {
            serverRunning = true
            btnToggle.text = getString(R.string.stop_server)
            tvUrl.text = url
            tvUrl.visibility = android.view.View.VISIBLE
            generateQr(url)
            webView.loadUrl("http://127.0.0.1:8888")
        }
    }

    private fun generateQr(text: String) {
        try {
            val writer = QRCodeWriter()
            val bitMatrix = writer.encode(text, BarcodeFormat.QR_CODE, 512, 512)
            val bitmap = Bitmap.createBitmap(512, 512, Bitmap.Config.RGB_565)
            for (x in 0 until 512) {
                for (y in 0 until 512) {
                    bitmap.setPixel(x, y,
                        if (bitMatrix[x, y]) android.graphics.Color.BLACK
                        else android.graphics.Color.WHITE)
                }
            }
            ivQr.setImageBitmap(bitmap)
            ivQr.visibility = android.view.View.VISIBLE
        } catch (_: Exception) {
            ivQr.visibility = android.view.View.GONE
        }
    }

    private fun onServerError(msg: String) {
        runOnUiThread {
            serverRunning = false
            btnToggle.text = getString(R.string.start_server)
            tvUrl.text = "Error: $msg"
        }
    }

    override fun onDestroy() {
        unregisterReceiver(serverReceiver)
        stopServer()
        super.onDestroy()
    }

    companion object {
        fun getLocalIpAddress(): String {
            NetworkInterface.getNetworkInterfaces()?.iterator()?.forEach { iface ->
                if (iface.isLoopback || !iface.isUp) return@forEach
                iface.inetAddresses?.iterator()?.forEach { addr ->
                    if (addr is Inet4Address && !addr.isLoopbackAddress) {
                        return addr.hostAddress ?: "127.0.0.1"
                    }
                }
            }
            return "127.0.0.1"
        }
    }
}
