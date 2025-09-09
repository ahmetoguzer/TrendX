#!/bin/bash
# TrendX Background Scheduler Script

echo "🚀 TrendX Background Scheduler Başlatılıyor..."

# Log dosyası oluştur
LOG_FILE="trendx.log"
PID_FILE="trendx.pid"

# Eski process'i durdur (varsa)
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "🛑 Eski process durduruluyor: $OLD_PID"
        kill $OLD_PID
    fi
    rm -f "$PID_FILE"
fi

# Background'da başlat
echo "⏰ Scheduler background'da başlatılıyor..."
nohup python3 -m trendx start > "$LOG_FILE" 2>&1 &

# Process ID'yi kaydet
echo $! > "$PID_FILE"

echo "✅ Scheduler başlatıldı!"
echo "📊 Process ID: $(cat $PID_FILE)"
echo "📝 Log dosyası: $LOG_FILE"
echo "🛑 Durdurmak için: kill \$(cat $PID_FILE)"
echo ""
echo "📋 Komutlar:"
echo "  - Log'u izle: tail -f $LOG_FILE"
echo "  - Durumu kontrol et: ps -p \$(cat $PID_FILE)"
echo "  - Durdur: kill \$(cat $PID_FILE)"
