#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$(cd "${SCRIPT_DIR}/../../assets" && pwd)"
BUILD_DIR="/tmp/purr_bridge_build"

# Detect Java 11+
if [ -d "/usr/lib/jvm/zulu-17" ]; then
    export JAVA_HOME="/usr/lib/jvm/zulu-17"
    export PATH="${JAVA_HOME}/bin:${PATH}"
elif [ -d "/usr/lib/jvm/zulu-11" ]; then
    export JAVA_HOME="/usr/lib/jvm/zulu-11"
    export PATH="${JAVA_HOME}/bin:${PATH}"
fi

SDK_ROOT="${HOME}/Android/Sdk"
BUILD_TOOLS_DIR="${SDK_ROOT}/build-tools/37.0.0"
PLATFORM_JAR="${SDK_ROOT}/platforms/android-33/android.jar"
KEYSTORE="${HOME}/.cache/purr/aurora_build/debug.keystore"

if [ ! -f "${PLATFORM_JAR}" ]; then
    echo "[!] Missing ${PLATFORM_JAR}" >&2
    exit 1
fi

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/classes" "${BUILD_DIR}/dex" "${ASSETS_DIR}"

echo "🐾 Compiling PurrBridgeHelper sources..."
javac -source 1.8 -target 1.8 -cp "${PLATFORM_JAR}" \
    -d "${BUILD_DIR}/classes" \
    "${SCRIPT_DIR}/src/dev/purr/bridge/BridgeReceiver.java"

echo "🐾 Converting bytecode to Dalvik dex..."
"${BUILD_TOOLS_DIR}/d8" --lib "${PLATFORM_JAR}" \
    --output "${BUILD_DIR}/dex" \
    "${BUILD_DIR}/classes/dev/purr/bridge"/*.class

echo "🐾 Packaging Android resources..."
"${BUILD_TOOLS_DIR}/aapt" package -f \
    -M "${SCRIPT_DIR}/AndroidManifest.xml" \
    -I "${PLATFORM_JAR}" \
    -F "${BUILD_DIR}/unaligned.apk"

(cd "${BUILD_DIR}/dex" && "${BUILD_TOOLS_DIR}/aapt" add "${BUILD_DIR}/unaligned.apk" classes.dex)

echo "🐾 4-byte zipaligning APK..."
"${BUILD_TOOLS_DIR}/zipalign" -p -f -v 4 "${BUILD_DIR}/unaligned.apk" "${BUILD_DIR}/aligned.apk"

echo "🐾 Signing PurrBridgeHelper with debug keystore..."
"${BUILD_TOOLS_DIR}/apksigner" sign \
    --ks "${KEYSTORE}" \
    --ks-pass pass:android \
    --key-pass pass:android \
    "${BUILD_DIR}/aligned.apk"

cp -f "${BUILD_DIR}/aligned.apk" "${ASSETS_DIR}/PurrBridgeHelper.apk"
chmod 644 "${ASSETS_DIR}/PurrBridgeHelper.apk"
echo "[✔] Successfully built and deployed PurrBridgeHelper.apk to ${ASSETS_DIR}/PurrBridgeHelper.apk"
