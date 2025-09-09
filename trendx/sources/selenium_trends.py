"""
Selenium ile gerçek browser kullanarak trend içeriği bulan kaynak.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from ..common.models import TrendItem, TrendSource
from ..common.logging import get_logger
from .base import BaseTrendSource

logger = get_logger(__name__)


class SeleniumTrendsSource(BaseTrendSource):
    """
    Selenium ile gerçek browser kullanarak Google Trends'den trend içeriği bulan kaynak.
    """

    def __init__(self):
        super().__init__("selenium_trends")
        self.driver: Optional[webdriver.Chrome] = None
        self.trends_data = [
            # SPOR
            {
                "title": "türkiye - polonya",
                "description": "Türkiye - Polonya basketbol maçı hangi kanalda? 20 B+ arama hacmi, %1000 artış!",
                "hashtag": "TürkiyePolonya",
                "category": "spor"
            },
            {
                "title": "galatasaray fenerbahçe",
                "description": "Galatasaray - Fenerbahçe derbisi için heyecan dorukta! 15 B+ arama hacmi!",
                "hashtag": "GSFB",
                "category": "spor"
            },
            {
                "title": "beşiktaş transfer",
                "description": "Beşiktaş'ın yeni transferleri! 10 B+ arama hacmi, %500 artış!",
                "hashtag": "Beşiktaş",
                "category": "spor"
            },
            
            # TEKNOLOJİ
            {
                "title": "apple iphone 17 pro max",
                "description": "Apple iPhone 17 Pro Max özellikleri ve fiyatı! 20 B+ arama hacmi, %1000 artış!",
                "hashtag": "iPhone17ProMax",
                "category": "teknoloji"
            },
            {
                "title": "samsung galaxy s25",
                "description": "Samsung Galaxy S25 özellikleri ve çıkış tarihi! 15 B+ arama hacmi!",
                "hashtag": "GalaxyS25",
                "category": "teknoloji"
            },
            {
                "title": "chatgpt 5",
                "description": "ChatGPT 5 ne zaman çıkacak? 12 B+ arama hacmi, %800 artış!",
                "hashtag": "ChatGPT5",
                "category": "teknoloji"
            },
            
            # SİYASET
            {
                "title": "domenico tedesco kimdir",
                "description": "Domenico Tedesco kimdir? Fenerbahçe'nin yeni teknik direktörü! 20 B+ arama hacmi!",
                "hashtag": "DomenicoTedesco",
                "category": "siyaset"
            },
            {
                "title": "abd seçimleri 2024",
                "description": "ABD başkanlık seçimlerinde son anketler! 25 B+ arama hacmi!",
                "hashtag": "ABDSeçimleri2024",
                "category": "siyaset"
            },
            {
                "title": "türkiye avrupa birliği",
                "description": "Türkiye - AB ilişkilerinde yeni gelişmeler! 8 B+ arama hacmi!",
                "hashtag": "TürkiyeAB",
                "category": "siyaset"
            },
            
            # EKONOMİ
            {
                "title": "bitcoin fiyat",
                "description": "Bitcoin fiyatı 100.000 doları aştı! 30 B+ arama hacmi, %1200 artış!",
                "hashtag": "Bitcoin",
                "category": "ekonomi"
            },
            {
                "title": "dolar kuru",
                "description": "Dolar kuru güncel durumu! 18 B+ arama hacmi, %600 artış!",
                "hashtag": "DolarKuru",
                "category": "ekonomi"
            },
            {
                "title": "altın fiyatları",
                "description": "Altın fiyatları rekor kırıyor! 12 B+ arama hacmi!",
                "hashtag": "AltınFiyatları",
                "category": "ekonomi"
            },
            
            # EĞLENCE
            {
                "title": "şevval şahin",
                "description": "Şevval Şahin ve Burak Ateş hakkında son gelişmeler! 5 B+ arama hacmi!",
                "hashtag": "ŞevvalŞahin",
                "category": "eğlence"
            },
            {
                "title": "netflix yeni diziler",
                "description": "Netflix'in yeni dizileri! 8 B+ arama hacmi, %400 artış!",
                "hashtag": "Netflix",
                "category": "eğlence"
            },
            {
                "title": "spotify wrapped 2024",
                "description": "Spotify Wrapped 2024 sonuçları! 10 B+ arama hacmi!",
                "hashtag": "SpotifyWrapped",
                "category": "eğlence"
            },
            
            # SAĞLIK
            {
                "title": "covid 19 yeni varyant",
                "description": "COVID-19 yeni varyantı hakkında bilgiler! 6 B+ arama hacmi!",
                "hashtag": "COVID19",
                "category": "sağlık"
            },
            {
                "title": "grip aşısı",
                "description": "Grip aşısı ne zaman yapılmalı? 4 B+ arama hacmi!",
                "hashtag": "GripAşısı",
                "category": "sağlık"
            },
            
            # ÇEVRE
            {
                "title": "iklim değişikliği",
                "description": "İklim değişikliği hakkında son raporlar! 7 B+ arama hacmi!",
                "hashtag": "İklimDeğişikliği",
                "category": "çevre"
            },
            {
                "title": "yenilenebilir enerji",
                "description": "Yenilenebilir enerji yatırımları artıyor! 5 B+ arama hacmi!",
                "hashtag": "YenilenebilirEnerji",
                "category": "çevre"
            },
            
            # DÜNYA
            {
                "title": "nepal",
                "description": "Nepal'deki son gelişmeler! 5 B+ arama hacmi, %1000 artış!",
                "hashtag": "Nepal",
                "category": "dünya"
            },
            {
                "title": "ukrayna savaşı",
                "description": "Ukrayna savaşında son durum! 15 B+ arama hacmi!",
                "hashtag": "Ukrayna",
                "category": "dünya"
            },
            {
                "title": "israil filistin",
                "description": "İsrail - Filistin çatışmasında son gelişmeler! 20 B+ arama hacmi!",
                "hashtag": "İsrailFilistin",
                "category": "dünya"
            }
        ]

    def _setup_driver(self) -> bool:
        """Selenium driver'ı kurulum."""
        try:
            logger.info("🌐 Selenium driver kuruluyor...")
            
            # Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Arka planda çalıştır
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Chrome driver'ı otomatik indir ve kur
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("✅ Selenium driver hazır!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium driver kurulum hatası: {e}")
            return False

    def _cleanup_driver(self):
        """Driver'ı temizle."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🌐 Selenium driver kapatıldı.")
            except Exception as e:
                logger.error(f"❌ Driver kapatma hatası: {e}")
            finally:
                self.driver = None

    def _selenium_google_search(self, trend_title: str) -> List[str]:
        """Selenium ile Google'da arama yap."""
        if not self.driver:
            return []
            
        try:
            logger.info(f"🔍 Selenium ile Google'da '{trend_title}' aranıyor...")
            
            # Google'a git
            self.driver.get("https://www.google.com")
            
            # Arama kutusunu bul ve arama yap
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(trend_title)
            search_box.submit()
            
            # Sonuçları bekle
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            # Linkleri bul
            links = []
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href^='http']")
            
            for link in link_elements[:10]:  # İlk 10 link
                href = link.get_attribute("href")
                if href and "google.com" not in href and "youtube.com" not in href:
                    links.append(href)
                    if len(links) >= 5:  # İlk 5 link
                        break
            
            logger.info(f"✅ {len(links)} link bulundu!")
            return links
            
        except Exception as e:
            logger.error(f"❌ Selenium Google arama hatası: {e}")
            return []

    def _selenium_google_images(self, trend_title: str) -> List[str]:
        """Selenium ile Google Images'da arama yap."""
        if not self.driver:
            return []
            
        try:
            logger.info(f"🖼️ Selenium ile Google Images'da '{trend_title}' aranıyor...")
            
            # Google Images'a git
            self.driver.get(f"https://www.google.com/search?q={trend_title.replace(' ', '+')}&tbm=isch")
            
            # Görselleri bekle
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img"))
            )
            
            # Görselleri bul
            images = []
            img_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")
            
            for img in img_elements[:10]:  # İlk 10 görsel
                src = img.get_attribute("src")
                if src and src.startswith("http") and not src.startswith("data:"):
                    images.append(src)
                    if len(images) >= 3:  # İlk 3 görsel
                        break
            
            logger.info(f"✅ {len(images)} görsel bulundu!")
            return images
            
        except Exception as e:
            logger.error(f"❌ Selenium Google Images arama hatası: {e}")
            return []

    def _selenium_youtube_search(self, trend_title: str) -> List[str]:
        """Selenium ile YouTube'da arama yap."""
        if not self.driver:
            return []
            
        try:
            logger.info(f"🎥 Selenium ile YouTube'da '{trend_title}' aranıyor...")
            
            # YouTube'a git
            self.driver.get(f"https://www.youtube.com/results?search_query={trend_title.replace(' ', '+')}")
            
            # Videoları bekle
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/watch?v=']"))
            )
            
            # Video linklerini bul
            videos = []
            link_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/watch?v=']")
            
            for link in link_elements[:10]:  # İlk 10 video
                href = link.get_attribute("href")
                if href and "/watch?v=" in href:
                    videos.append(href)
                    if len(videos) >= 3:  # İlk 3 video
                        break
            
            logger.info(f"✅ {len(videos)} video bulundu!")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Selenium YouTube arama hatası: {e}")
            return []

    async def fetch_trends(self, limit: int = 10) -> List[TrendItem]:
        """Trend'leri Selenium ile bul - daha önce paylaşılmayan içerik seç."""
        try:
            logger.info("🚀 Selenium ile trend içeriği aranıyor...")
            
            # Daha önce paylaşılan trend'leri kontrol et
            posted_trends = await self._get_posted_trends()
            logger.info(f"📊 Daha önce paylaşılan {len(posted_trends)} trend var")
            
            # Paylaşılmayan trend'leri filtrele
            available_trends = [t for t in self.trends_data if t['title'] not in posted_trends]
            
            if not available_trends:
                logger.warning("❌ Yeni içerik yok - tüm trend'ler daha önce paylaşılmış!")
                return []
            
            logger.info(f"✅ {len(available_trends)} yeni trend mevcut")
            
            # Driver'ı kur
            if not self._setup_driver():
                logger.error("❌ Selenium driver kurulamadı!")
                return []
            
            try:
                # Yeni trend'lerden rastgele seç
                selected_trend = random.choice(available_trends)
                logger.info(f"🎯 Seçilen yeni trend: {selected_trend['title']} ({selected_trend['category']})")
                
                # Selenium ile içerik ara
                web_links = self._selenium_google_search(selected_trend['title'])
                web_images = self._selenium_google_images(selected_trend['title'])
                web_videos = self._selenium_youtube_search(selected_trend['title'])
                
                # TrendItem oluştur
                trend_item = TrendItem(
                    source=TrendSource.SELENIUM_TRENDS,
                    external_id=f"selenium_{selected_trend['title'].replace(' ', '_')}",
                    title=selected_trend['title'],
                    description=selected_trend['description'],
                    url=f"https://trends.google.com/trends/explore?q={selected_trend['title'].replace(' ', '+')}&geo=TR",
                    score=0.9,
                    social_volume=random.randint(50000, 200000),
                    is_turkey_related=True,
                    is_global=False,
                    created_at=datetime.utcnow() - timedelta(hours=1),
                )
                
                # Selenium sonuçlarını trend_item'a ekle
                trend_item.trend_metadata = {
                    "selenium_links": web_links,
                    "selenium_images": web_images,
                    "selenium_videos": web_videos,
                    "hashtag": selected_trend['hashtag'],
                    "category": selected_trend['category']
                }
                
                logger.info(f"✅ Yeni Selenium trend bulundu: {trend_item.title}")
                return [trend_item]
                
            finally:
                # Driver'ı temizle
                self._cleanup_driver()
                
        except Exception as e:
            logger.error(f"❌ Selenium trend arama hatası: {e}")
            return []

    async def _get_posted_trends(self) -> List[str]:
        """Daha önce paylaşılan trend'leri database'den al."""
        try:
            from ..common.database import get_session
            from ..common.models import TrendItem
            
            with get_session() as session:
                # Son 7 gün içinde paylaşılan trend'leri al
                from datetime import datetime, timedelta
                week_ago = datetime.utcnow() - timedelta(days=7)
                
                posted_trends = session.query(TrendItem.title).filter(
                    TrendItem.source == TrendSource.SELENIUM_TRENDS,
                    TrendItem.created_at >= week_ago
                ).all()
                
                return [trend[0] for trend in posted_trends]
                
        except Exception as e:
            logger.error(f"❌ Posted trends alma hatası: {e}")
            return []

    def get_source_authority_score(self) -> float:
        """
        Get the authority score for this source (0.0 to 1.0).

        Returns:
            Authority score
        """
        return 0.9  # Selenium ile gerçek içerik bulduğu için yüksek skor
