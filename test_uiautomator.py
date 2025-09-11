#!/usr/bin/env python3
"""
UIAutomator2 Twitter Publisher Test
"""
import asyncio
import sys
import os

# Proje root'unu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trendx.publisher.uiautomator_twitter_publisher import UIAutomatorTwitterPublisher
from trendx.common.models import TweetContent

async def test_uiautomator_publisher():
    """UIAutomator2 Publisher'ı test et"""
    print("🤖 UIAutomator2 Twitter Publisher Test Başlatılıyor...")
    
    # Test tweet içeriği
    test_content = TweetContent(
        turkish_text="UIAutomator2 ile Android Twitter uygulamasından test tweet! 🚀",
        english_text="Test tweet from Android Twitter app via UIAutomator2! 🚀",
        hashtags="#UIAutomator2 #Android #Twitter #Automation #TrendX",
        media_url="https://picsum.photos/800/600?random=1"
    )
    
    # Publisher'ı oluştur
    publisher = UIAutomatorTwitterPublisher()
    
    try:
        # Tweet'i gönder
        result = await publisher.publish_tweet(test_content)
        
        if result.success:
            print(f"✅ Tweet başarıyla gönderildi!")
            print(f"📱 Tweet ID: {result.tweet_id}")
            print(f"🔗 UIAutomator2 Publisher kullanıldı")
        else:
            print(f"❌ Tweet gönderilemedi: {result.error}")
            
    except Exception as e:
        print(f"💥 Test hatası: {e}")

if __name__ == "__main__":
    asyncio.run(test_uiautomator_publisher())

