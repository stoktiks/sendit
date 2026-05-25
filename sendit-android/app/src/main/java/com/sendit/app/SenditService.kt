package com.sendit.app

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader

class SenditService : Service() {

    private var serverProcess: Process? = null
    private var monitorThread: Thread? = null

    companion object {
        const val ACTION_START = "com.sendit.action.START"
        const val ACTION_STOP = "com.sendit.action.STOP"
        const val CHANNEL_ID = "sendit_server"
        const val NOTIFICATION_ID = 1
        private const val SERVER_PORT = 8888
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> startServer()
            ACTION_STOP -> stopServer()
        }
        return START_NOT_STICKY
    }

    private fun startServer() {
        if (serverProcess != null) return

        val binaryPath = ensureBinary()
        if (binaryPath == null) {
            notifyError("Failed to extract binary")
            return
        }

        try {
            val pb = ProcessBuilder(
                binaryPath, "web", SERVER_PORT.toString()
            )
            pb.directory(filesDir)
            pb.environment().put("HOME", filesDir.absolutePath)
            serverProcess = pb.start()

            startForeground(NOTIFICATION_ID, buildNotification())

            // Monitor: wait for server to print URL, then notify activity
            monitorThread = Thread {
                try {
                    val reader = BufferedReader(InputStreamReader(serverProcess!!.inputStream))
                    var line: String?
                    while (reader.readLine().also { line = it } != null) {
                        val l = line ?: continue
                        // Look for the URL line (starts with 🔗)
                        if (l.contains("http://")) {
                            val url = l.substring(l.indexOf("http://"))
                            notifyReady(url)
                            break
                        }
                    }
                    // Wait for process to finish
                    serverProcess?.waitFor()
                } catch (_: Exception) {}
            }.also { it.start() }

        } catch (e: Exception) {
            notifyError("Failed to start server: ${e.message}")
        }
    }

    private fun stopServer() {
        serverProcess?.destroy()
        serverProcess?.waitFor()
        serverProcess = null
        monitorThread?.interrupt()
        monitorThread = null
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun ensureBinary(): String? {
        val destFile = File(filesDir, "sendit-linux-arm64")
        if (destFile.exists() && destFile.length() > 100_000) {
            return destFile.absolutePath
        }

        return try {
            assets.open("sendit-linux-arm64").use { input ->
                destFile.outputStream().use { output ->
                    input.copyTo(output)
                }
            }
            // Make executable
            Runtime.getRuntime().exec(arrayOf("chmod", "+x", destFile.absolutePath)).waitFor()
            destFile.absolutePath
        } catch (e: Exception) {
            null
        }
    }

    private fun buildNotification(): Notification {
        val pendingIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
            },
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Create channel for Android 8+
        if (Build.VERSION.SDK_INT >= 26) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notification_channel),
                NotificationManager.IMPORTANCE_LOW
            )
            val nm = getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(channel)
        }

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("sendit")
            .setContentText(getString(R.string.sharing_via))
            .setSmallIcon(android.R.drawable.ic_menu_share)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .build()
    }

    private fun notifyReady(url: String) {
        val ip = MainActivity.getLocalIpAddress()
        val displayUrl = "http://$ip:$SERVER_PORT"
        sendBroadcast(Intent("com.sendit.SERVER_READY").apply {
            putExtra("url", displayUrl)
        })
    }

    private fun notifyError(msg: String) {
        sendBroadcast(Intent("com.sendit.SERVER_ERROR").apply {
            putExtra("message", msg)
        })
    }

    override fun onDestroy() {
        stopServer()
        super.onDestroy()
    }
}
