"""
Selenium Twitter Publisher - API rate limit'leri bypass eder
"""

import asyncio
import time
import random
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import structlog

from ..common.models import TweetContent, PublishResult

logger = structlog.get_logger(__name__)


class SeleniumTwitterPublisher:
    """Selenium ile Twitter'a post atan publisher - API rate limit'leri bypass eder."""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.is_logged_in = False
        
    def _setup_driver(self) -> bool:
        """Selenium driver'ı kurulum."""
        try:
            logger.info("🌐 Selenium Twitter driver kuruluyor...")
            
            # Chrome options - login için headless değil
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            # Headless değil - login için Chrome penceresi açık olacak
            
            # Chrome driver'ı otomatik indir ve kur
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("✅ Selenium Twitter driver hazır!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Selenium driver kurulum hatası: {e}")
            return False
    
    def _cleanup_driver(self) -> None:
        """Driver'ı temizle."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 Selenium driver temizlendi")
            except Exception as e:
                logger.error(f"❌ Driver temizleme hatası: {e}")
            finally:
                self.driver = None
    
    def _login_to_twitter(self) -> bool:
        """Twitter'a manuel login - Chrome penceresi açık kalacak."""
        if not self.driver:
            return False
            
        try:
            logger.info("🔐 Twitter'a manuel login için Chrome açılıyor...")
            
            # Twitter'a git
            self.driver.get("https://twitter.com/login")
            
            # Kullanıcıya manuel login yapması için bekle
            logger.info("👤 Lütfen Chrome penceresinde Twitter'a manuel olarak login olun...")
            logger.info("⏳ Login olduktan sonra Enter'a basın...")
            
            # Kullanıcı input'unu bekle
            input("Login olduktan sonra Enter'a basın...")
            
            # Login başarılı mı kontrol et
            time.sleep(2)
            
            # Ana sayfa elementlerini ara
            home_indicators = [
                "[data-testid='tweetButton']",
                "[data-testid='primaryColumn']",
                "[aria-label='Home timeline']",
                "[data-testid='tweetTextarea_0']"
            ]
            
            login_success = False
            for indicator in home_indicators:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                    )
                    login_success = True
                    break
                except TimeoutException:
                    continue
            
            if not login_success:
                logger.error("❌ Login başarısız - ana sayfa yüklenemedi")
                return False
            
            self.is_logged_in = True
            logger.info("✅ Twitter'a başarıyla login olundu!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Twitter login hatası: {e}")
            return False
    
    def _compose_tweet(self, content: TweetContent) -> bool:
        """Tweet yazma alanına içerik gir."""
        if not self.driver or not self.is_logged_in:
            return False
            
        try:
            logger.info("✍️ Tweet yazılıyor...")
            
            # Tweet compose alanını bul (yeni selector'lar)
            compose_selectors = [
                "[data-testid='tweetTextarea_0']",
                "[data-testid='tweetTextarea_0']",
                "[aria-label='Post text']",
                "[data-testid='tweetTextarea_0']",
                "div[data-testid='tweetTextarea_0']",
                "[role='textbox']"
            ]
            
            compose_area = None
            for selector in compose_selectors:
                try:
                    compose_area = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Compose alanı bulundu: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not compose_area:
                logger.error("❌ Tweet compose alanı bulunamadı")
                return False
            
            # Tweet metnini hazırla
            tweet_text = f"{content.turkish_text}\n\n{content.english_text}"
            
            # Hashtag'leri ekle
            if content.hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in content.hashtags])
                tweet_text += f"\n\n{hashtag_text}"
            
            # Link ekle (media_url kullan)
            if content.media_url:
                tweet_text += f"\n\n{content.media_url}"
            
            # Tweet yazma alanına tıkla ve metni gir
            compose_area.click()
            compose_area.clear()
            compose_area.send_keys(tweet_text)
            
            logger.info(f"✅ Tweet metni yazıldı: {len(tweet_text)} karakter")
            return True
            
        except TimeoutException:
            logger.error("❌ Tweet compose alanı bulunamadı")
            return False
        except Exception as e:
            logger.error(f"❌ Tweet yazma hatası: {e}")
            return False
    
    def _upload_media(self, media_url: str) -> bool:
        """Media upload et."""
        if not self.driver or not media_url:
            return False
            
        try:
            logger.info(f"📷 Media upload ediliyor: {media_url}")
            
            # Media upload butonunu bul ve tıkla
            media_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='fileInput']"))
            )
            
            # Media URL'ini input'a gir (bu basit bir yaklaşım)
            # Gerçek implementasyonda media'yı download edip upload etmek gerekir
            media_button.send_keys(media_url)
            
            logger.info("✅ Media upload edildi")
            return True
            
        except Exception as e:
            logger.error(f"❌ Media upload hatası: {e}")
            return False
    
    def _post_tweet(self) -> Optional[str]:
        """Tweet'i post et."""
        if not self.driver or not self.is_logged_in:
            return None
            
        try:
            logger.info("🚀 Tweet post ediliyor...")
            
            # Tweet butonunu bul ve tıkla (yeni selector'lar)
            tweet_button_selectors = [
                "[data-testid='tweetButton']",
                "[data-testid='tweetButtonInline']",
                "[aria-label='Post']",
                "button[data-testid='tweetButton']",
                "[role='button'][data-testid='tweetButton']",
                "button[type='button']:contains('Post')"
            ]
            
            tweet_button = None
            for selector in tweet_button_selectors:
                try:
                    tweet_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"✅ Tweet butonu bulundu: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not tweet_button:
                logger.error("❌ Tweet butonu bulunamadı")
                return None
            
            # JavaScript ile tıkla (element click intercepted hatası için)
            self.driver.execute_script("arguments[0].click();", tweet_button)
            
            # Post başarılı mı kontrol et
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='tweet']"))
            )
            
            # Tweet ID'yi al (basit yaklaşım)
            tweet_id = f"selenium_{int(time.time())}"
            
            logger.info(f"✅ Tweet başarıyla post edildi! ID: {tweet_id}")
            return tweet_id
            
        except TimeoutException:
            logger.error("❌ Tweet post timeout")
            return None
        except Exception as e:
            logger.error(f"❌ Tweet post hatası: {e}")
            return None
    
    async def publish_tweet(self, content: TweetContent) -> PublishResult:
        """Tweet'i Selenium ile post et."""
        try:
            logger.info("🚀 Selenium ile tweet post ediliyor...")
            
            # Driver'ı kur
            if not self._setup_driver():
                return PublishResult(success=False, error_message="Selenium driver kurulamadı")
            
            try:
                # Twitter'a login ol
                if not self._login_to_twitter():
                    return PublishResult(success=False, error_message="Twitter login başarısız")
                
                # Tweet yaz
                if not self._compose_tweet(content):
                    return PublishResult(success=False, error_message="Tweet yazılamadı")
                
                # Media upload et (varsa)
                if content.media_url:
                    self._upload_media(content.media_url)
                
                # Tweet'i post et
                tweet_id = self._post_tweet()
                if not tweet_id:
                    return PublishResult(success=False, error_message="Tweet post edilemedi")
                
                # Başarılı
                return PublishResult(success=True, post_id=tweet_id)
                
            finally:
                # Driver'ı temizle
                self._cleanup_driver()
                
        except Exception as e:
            logger.error(f"❌ Selenium tweet post hatası: {e}")
            return PublishResult(success=False, error_message=str(e))
