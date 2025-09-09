#!/bin/bash
# TrendX Background Scheduler Durdurma Script

echo "🛑 TrendX Background Scheduler Durduruluyor..."

PID_FILE="trendx.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 Process durduruluyor: $PID"
        kill $PID
        sleep 2
        
        # Hala çalışıyorsa force kill
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚡ Force kill: $PID"
            kill -9 $PID
        fi
        
        echo "✅ Scheduler durduruldu!"
    else
        echo "❌ Process zaten durmuş: $PID"
    fi
    rm -f "$PID_FILE"
else
    echo "❌ PID dosyası bulunamadı: $PID_FILE"
fi
