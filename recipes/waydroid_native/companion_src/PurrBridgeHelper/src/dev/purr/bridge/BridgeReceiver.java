package dev.purr.bridge;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.database.sqlite.SQLiteDatabase;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.lang.reflect.Field;
import java.util.Arrays;

/**
 * 🐾 PurrBridgeHelper — Synchronous Two-Way Android <-> Linux IPC Receiver
 * Communicates headlessly with the host CLI via `am broadcast -W`.
 * Returns rich structured JSON in resultData for instant CLI parsing.
 */
public class BridgeReceiver extends BroadcastReceiver {
    private static final String TAG = "PurrBridge";
    public static final String BRIDGE_VERSION = "1.0.0";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getStringExtra("action");
        if (action == null || action.trim().isEmpty()) {
            action = "ping";
        }

        JSONObject resp = new JSONObject();
        Bundle resultExtras = new Bundle();

        try {
            resp.put("status", "ok");
            resp.put("action", action);
            resp.put("version", BRIDGE_VERSION);
            resp.put("timestamp", System.currentTimeMillis());

            switch (action.toLowerCase()) {
                case "ping":
                    handlePing(context, resp);
                    break;

                case "query_app":
                    handleQueryApp(context, intent, resp);
                    break;

                case "detach_play_store":
                    handleDetachPlayStore(context, intent, resp);
                    break;

                case "aurora_blacklist":
                    handleAuroraBlacklist(context, intent, resp);
                    break;

                case "force_stop":
                    handleForceStop(context, intent, resp);
                    break;

                default:
                    resp.put("status", "error");
                    resp.put("error", "UNKNOWN_ACTION: " + action);
                    setResult(Activity.RESULT_CANCELED, resp.toString(), resultExtras);
                    return;
            }

            setResult(Activity.RESULT_OK, resp.toString(), resultExtras);

        } catch (Throwable t) {
            Log.e(TAG, "Exception during bridge action " + action, t);
            try {
                resp.put("status", "error");
                resp.put("error", t.getClass().getSimpleName() + ": " + t.getMessage());
            } catch (Exception ignored) {}
            setResult(Activity.RESULT_CANCELED, resp.toString(), resultExtras);
        }
    }

    private void handlePing(Context context, JSONObject resp) throws Exception {
        resp.put("os_build", Build.DISPLAY);
        resp.put("android_version", Build.VERSION.RELEASE);
        resp.put("sdk_int", Build.VERSION.SDK_INT);
        resp.put("cpu_abi", Build.CPU_ABI);
        if (Build.SUPPORTED_ABIS != null) {
            resp.put("supported_abis", new JSONArray(Arrays.asList(Build.SUPPORTED_ABIS)));
        }
    }

    private void handleQueryApp(Context context, Intent intent, JSONObject resp) throws Exception {
        String pkg = intent.getStringExtra("package");
        if (pkg == null || pkg.trim().isEmpty()) {
            resp.put("status", "error");
            resp.put("error", "MISSING_PACKAGE_ARGUMENT");
            return;
        }

        PackageManager pm = context.getPackageManager();
        try {
            PackageInfo pi = pm.getPackageInfo(pkg, PackageManager.GET_META_DATA);
            resp.put("installed", true);
            resp.put("package", pkg);
            resp.put("versionName", pi.versionName != null ? pi.versionName : "");
            resp.put("versionCode", pi.getLongVersionCode());

            ApplicationInfo ai = pi.applicationInfo;
            String primaryCpuAbi = "unknown";
            try {
                Field f = ApplicationInfo.class.getField("primaryCpuAbi");
                Object val = f.get(ai);
                if (val instanceof String) {
                    primaryCpuAbi = (String) val;
                }
            } catch (Throwable ignored) {}
            resp.put("primaryCpuAbi", primaryCpuAbi != null ? primaryCpuAbi : "unknown");
            resp.put("sourceDir", ai.sourceDir != null ? ai.sourceDir : "");

            String installer = "unknown";
            try {
                installer = pm.getInstallerPackageName(pkg);
            } catch (Throwable ignored) {}
            resp.put("installer", installer != null ? installer : "unknown");

        } catch (PackageManager.NameNotFoundException e) {
            resp.put("installed", false);
            resp.put("package", pkg);
            resp.put("message", "Package not installed");
        }
    }

    private void handleDetachPlayStore(Context context, Intent intent, JSONObject resp) throws Exception {
        String pkg = intent.getStringExtra("package");
        if (pkg == null || pkg.trim().isEmpty()) {
            resp.put("status", "error");
            resp.put("error", "MISSING_PACKAGE_ARGUMENT");
            return;
        }

        int totalPurged = 0;
        String[] dbPaths = {
            "/data/data/com.android.vending/databases/library.db",
            "/data/data/com.android.vending/databases/localappstate.db",
            "/data/data/com.android.vending/databases/auto_update.db"
        };

        for (String dbPath : dbPaths) {
            File f = new File(dbPath);
            if (f.exists()) {
                try {
                    SQLiteDatabase db = SQLiteDatabase.openDatabase(dbPath, null, SQLiteDatabase.OPEN_READWRITE);
                    if (dbPath.endsWith("library.db")) {
                        totalPurged += db.delete("ownership", "doc_id = ?", new String[]{pkg});
                    } else if (dbPath.endsWith("localappstate.db")) {
                        totalPurged += db.delete("appstate", "package_name = ?", new String[]{pkg});
                    } else if (dbPath.endsWith("auto_update.db")) {
                        totalPurged += db.delete("auto_update", "pk = ?", new String[]{pkg});
                    }
                    db.close();
                } catch (Throwable t) {
                    Log.w(TAG, "Bridge cannot access db directly: " + dbPath + " (" + t.getMessage() + ")");
                }
            }
        }

        resp.put("package", pkg);
        resp.put("purged_db_entries", totalPurged);

        try {
            ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            if (am != null) {
                am.killBackgroundProcesses("com.android.vending");
            }
        } catch (Throwable ignored) {}
    }

    private void handleAuroraBlacklist(Context context, Intent intent, JSONObject resp) throws Exception {
        String pkg = intent.getStringExtra("package");
        if (pkg == null || pkg.trim().isEmpty()) {
            resp.put("status", "error");
            resp.put("error", "MISSING_PACKAGE_ARGUMENT");
            return;
        }

        resp.put("package", pkg);
        resp.put("note", "Aurora blacklist configured via host sync & preferences");
    }

    private void handleForceStop(Context context, Intent intent, JSONObject resp) throws Exception {
        String pkg = intent.getStringExtra("package");
        if (pkg == null || pkg.trim().isEmpty()) {
            resp.put("status", "error");
            resp.put("error", "MISSING_PACKAGE_ARGUMENT");
            return;
        }

        try {
            ActivityManager am = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            if (am != null) {
                am.killBackgroundProcesses(pkg);
            }
            resp.put("package", pkg);
            resp.put("stopped", true);
        } catch (Throwable t) {
            resp.put("status", "error");
            resp.put("error", t.getMessage());
        }
    }
}
