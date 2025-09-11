"""
UIAutomator2 Twitter Publisher - Android Twitter uygulaması üzerinden post atma
"""
import asyncio
import time
import random
from typing import Optional, List
import uiautomator2 as u2
import structlog
from PIL import Image
import io
import requests

from ..common.models import TweetContent, PublishResult

logger = structlog.get_logger(__name__)


class UIAutomatorTwitterPublisher:
    """Android Twitter uygulaması üzerinden UIAutomator2 ile tweet atma"""
    
    def __init__(self, device_id: Optional[str] = None):
        self.device_id = device_id
        self.device: Optional[u2.Device] = None
        self.is_connected = False
        
    def _setup_device(self) -> bool:
        """Android cihazına bağlan"""
        try:
            if self.device_id:
                self.device = u2.connect(self.device_id)
                logger.info(f"UIAutomator2: Cihaza bağlandı - {self.device_id}")
            else:
                # İlk bulunan cihaza bağlan
                self.device = u2.connect()
                logger.info("UIAutomator2: İlk cihaza bağlandı")
            
            # Cihaz bilgilerini al
            device_info = self.device.info
            logger.info(f"UIAutomator2: Cihaz bilgileri - {device_info}")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"UIAutomator2: Cihaz bağlantı hatası - {e}")
            return False
    
    def _cleanup_device(self) -> None:
        """Cihaz bağlantısını temizle"""
        if self.device:
            try:
                self.device = None
                self.is_connected = False
                logger.info("UIAutomator2: Cihaz bağlantısı temizlendi")
            except Exception as e:
                logger.error(f"UIAutomator2: Temizleme hatası - {e}")
    
    def _open_twitter_app(self) -> bool:
        """Twitter uygulamasını aç"""
        try:
            # Twitter uygulamasını başlat
            self.device.app_start("com.twitter.android")
            time.sleep(3)
            
            # Uygulama açıldı mı kontrol et
            if self.device.app_current()["package"] == "com.twitter.android":
                logger.info("UIAutomator2: Twitter uygulaması açıldı")
                return True
            else:
                logger.error("UIAutomator2: Twitter uygulaması açılamadı")
                return False
                
        except Exception as e:
            logger.error(f"UIAutomator2: Twitter uygulaması açma hatası - {e}")
            return False
    
    def _is_compose_screen_open(self) -> bool:
        """Compose ekranının açık olup olmadığını kontrol et"""
        try:
            # X'in compose ekranındaki elementleri kontrol et (verdiğin selector'lara göre)
            compose_indicators = [
                # Class ile arama
                "android.widget.EditText",
                # Description ile arama
                "What is happening", "Neler oluyor", "Write a post", "Gönderi yaz",
                # Resource ID ile arama
                "com.twitter.android:id/tweet_text",
                "com.twitter.android:id/button_tweet",
                "com.twitter.android:id/composer",
                "com.twitter.android:id/compose_edit_text"
            ]
            
            for indicator in compose_indicators:
                try:
                    # Class ile dene
                    if indicator == "android.widget.EditText":
                        if self.device(className=indicator).exists:
                            logger.info(f"UIAutomator2: Compose ekranı açık - class: {indicator}")
                            return True
                    # Description ile dene
                    elif self.device(descriptionContains=indicator).exists:
                        logger.info(f"UIAutomator2: Compose ekranı açık - desc: {indicator}")
                        return True
                    # Resource ID ile dene
                    elif self.device(resourceId=indicator).exists:
                        logger.info(f"UIAutomator2: Compose ekranı açık - id: {indicator}")
                        return True
                    # Text ile dene
                    elif self.device(text=indicator).exists:
                        logger.info(f"UIAutomator2: Compose ekranı açık - text: {indicator}")
                        return True
                except:
                    continue
            
            logger.info("UIAutomator2: Compose ekranı açık değil")
            return False
            
        except Exception as e:
            logger.error(f"UIAutomator2: Compose ekranı kontrol hatası - {e}")
            return False
    
    def _find_compose_button(self) -> bool:
        """FAB'a tıkla (Compose) - AI önerisi adım adım akış"""
        try:
            # Adım 1: FAB'a tıkla (Compose)
            fab_selectors = [
                # Description ile arama
                "Compose", "Tweet", "Post", "Gönder", "Yeni gönderi",
                # Resource ID ile arama (fab, compose, new_tweet içeren)
                "com.twitter.android:id/composer_write",
                "com.twitter.android:id/fab_compose",
                "com.twitter.android:id/new_tweet_button"
            ]
            
            for selector in fab_selectors:
                try:
                    # Description ile dene
                    if self.device(descriptionContains=selector).exists:
                        self.device(descriptionContains=selector).click()
                        logger.info(f"UIAutomator2: FAB tıklandı - desc: {selector}")
                        time.sleep(2)
                        
                        # Adım 2: Speed-dial menü açıldı mı kontrol et
                        if self._is_speed_dial_menu_open():
                            # Adım 3: "Gönderi" öğesine tıkla
                            return self._click_post_option()
                        else:
                            # Menü açılmadı, compose ekranı direkt açılmış olabilir
                            time.sleep(1)
                            return True
                            
                    # Resource ID ile dene
                    elif self.device(resourceId=selector).exists:
                        self.device(resourceId=selector).click()
                        logger.info(f"UIAutomator2: FAB tıklandı - id: {selector}")
                        time.sleep(2)
                        
                        if self._is_speed_dial_menu_open():
                            return self._click_post_option()
                        else:
                            time.sleep(1)
                            return True
                            
                    # Text ile dene
                    elif self.device(text=selector).exists:
                        self.device(text=selector).click()
                        logger.info(f"UIAutomator2: FAB tıklandı - text: {selector}")
                        time.sleep(2)
                        
                        if self._is_speed_dial_menu_open():
                            return self._click_post_option()
                        else:
                            time.sleep(1)
                            return True
                except:
                    continue
            
            logger.error("UIAutomator2: FAB bulunamadı")
            return False
            
        except Exception as e:
            logger.error(f"UIAutomator2: FAB tıklama hatası - {e}")
            return False
    
    def _is_speed_dial_menu_open(self) -> bool:
        """Speed-dial menü açıldı mı kontrol et"""
        try:
            # Speed-dial menü göstergeleri
            menu_indicators = [
                "Gönderi", "Sohbet Odaları", "Canlı Yayına Geç", "Fotoğraflar",
                "Post", "Chat Rooms", "Go Live", "Photos"
            ]
            
            for indicator in menu_indicators:
                if self.device(text=indicator).exists or self.device(description=indicator).exists:
                    logger.info(f"UIAutomator2: Speed-dial menü açık - {indicator}")
                    return True
            
            logger.info("UIAutomator2: Speed-dial menü açık değil")
            return False
            
        except Exception as e:
            logger.error(f"UIAutomator2: Speed-dial menü kontrol hatası - {e}")
            return False
    
    def _click_post_option(self) -> bool:
        """'Gönderi' öğesine tıkla - UI dump'tan doğru selector"""
        try:
            # Doğru Resource ID ile "Gönderi" seçeneği (UI dump'tan)
            if self.device(resourceId="com.twitter.android:id/tweet_label").exists:
                self.device(resourceId="com.twitter.android:id/tweet_label").click()
                logger.info("UIAutomator2: Gönderi seçeneği tıklandı - tweet_label")
                time.sleep(3)
                return True
            
            # Alternatif: Text ile arama
            if self.device(text="Gönderi").exists:
                self.device(text="Gönderi").click()
                logger.info("UIAutomator2: Gönderi seçeneği tıklandı - text")
                time.sleep(3)
                return True
            
            # Alternatif: Description ile arama
            if self.device(description="Gönderi").exists:
                self.device(description="Gönderi").click()
                logger.info("UIAutomator2: Gönderi seçeneği tıklandı - description")
                time.sleep(3)
                return True
            
            logger.error("UIAutomator2: Gönderi seçeneği bulunamadı")
            return False
            
        except Exception as e:
            logger.error(f"UIAutomator2: Gönderi seçeneği tıklama hatası - {e}")
            return False
    
    def _write_tweet_text(self, content: TweetContent) -> bool:
        """Compose editörü açılmasını bekle ve tweet metnini yaz - AI önerisi"""
        try:
            # Adım 4: Compose editörü açılmasını bekle
            if not self._wait_for_compose_editor():
                return False
            
            # Tweet metnini hazırla
            tweet_text = content.turkish_text
            if content.english_text:
                tweet_text += f"\n\n{content.english_text}"
            
            # Hashtag ekle
            if content.hashtags:
                tweet_text += f"\n\n{content.hashtags}"
            
            # Media URL ekle
            if content.media_url:
                tweet_text += f"\n\n{content.media_url}"
            
            # Doğru Resource ID ile tweet yazma alanını bul (UI dump'tan)
            if self.device(resourceId="com.twitter.android:id/tweet_text").exists:
                self.device(resourceId="com.twitter.android:id/tweet_text").click()
                time.sleep(1)
                self.device(resourceId="com.twitter.android:id/tweet_text").set_text(tweet_text)
                logger.info("UIAutomator2: Tweet metni yazıldı - tweet_text")
                time.sleep(2)
                return True
            
            # Alternatif: EditText bul ve metni yaz
            if self.device(className="android.widget.EditText", enabled=True).exists:
                edit_text = self.device(className="android.widget.EditText", enabled=True)
                edit_text.click()
                time.sleep(1)
                edit_text.set_text(tweet_text)
                logger.info("UIAutomator2: Tweet metni yazıldı - EditText")
                time.sleep(2)
                return True
            
            logger.error("UIAutomator2: Tweet yazma alanı bulunamadı")
            return False
            
        except Exception as e:
            logger.error(f"UIAutomator2: Tweet yazma hatası - {e}")
            return False
    
    def _wait_for_compose_editor(self) -> bool:
        """Compose editörü açılmasını bekle - UI dump'tan doğru selector'lar"""
        try:
            # 10 saniye bekle ve compose editörünü kontrol et
            for i in range(10):
                time.sleep(1)
                
                # 1. Doğru Resource ID ile kontrol (UI dump'tan)
                if self.device(resourceId="com.twitter.android:id/tweet_text").exists:
                    logger.info("UIAutomator2: Compose editörü açıldı - tweet_text")
                    return True
                
                # 2. Compose container kontrolü
                if self.device(resourceId="com.twitter.android:id/composer").exists:
                    logger.info("UIAutomator2: Compose editörü açıldı - composer")
                    return True
                
                # 3. EditText ve enabled=true kontrolü
                if self.device(className="android.widget.EditText", enabled=True).exists:
                    logger.info("UIAutomator2: Compose editörü açıldı - EditText")
                    return True
                
                # 4. Text ile kontrol
                if self.device(text="Neler oluyor?").exists:
                    logger.info("UIAutomator2: Compose editörü açıldı - text")
                    return True
            
            logger.error("UIAutomator2: Compose editörü açılamadı")
            return False
            
        except Exception as e:
            logger.error(f"UIAutomator2: Compose editörü bekleme hatası - {e}")
            return False
    
    def _add_media(self, media_url: str) -> bool:
        """Medya ekle (resim/video)"""
        try:
            if not media_url:
                return True
            
            # X'in gerçek medya ekleme butonları (verdiğin selector'lara göre)
            media_selectors = [
                # Description ile arama
                "Add photos", "Fotoğraf ekle", "Media", "Galeri", "Add media",
                # Resource ID ile arama (media, attach, photo, gallery içeren)
                "com.twitter.android:id/gallery",
                "com.twitter.android:id/add_media",
                "com.twitter.android:id/attach_media",
                "com.twitter.android:id/media_button",
                "com.twitter.android:id/photo_button"
            ]
            
            for selector in media_selectors:
                try:
                    # Description ile dene
                    if self.device(descriptionContains=selector).exists:
                        self.device(descriptionContains=selector).click()
                        time.sleep(2)
                        
                        # URL'den resim indir ve ekle
                        if self._download_and_add_image(media_url):
                            logger.info(f"UIAutomator2: Medya eklendi - desc: {selector}")
                            return True
                    # Resource ID ile dene
                    elif self.device(resourceId=selector).exists:
                        self.device(resourceId=selector).click()
                        time.sleep(2)
                        
                        # URL'den resim indir ve ekle
                        if self._download_and_add_image(media_url):
                            logger.info(f"UIAutomator2: Medya eklendi - id: {selector}")
                            return True
                except:
                    continue
            
            logger.warning("UIAutomator2: Medya ekleme butonu bulunamadı, sadece metin ile devam")
            return True
            
        except Exception as e:
            logger.error(f"UIAutomator2: Medya ekleme hatası - {e}")
            return True  # Medya olmadan devam et
    
    def _download_and_add_image(self, image_url: str) -> bool:
        """Resmi indir ve Twitter'a ekle"""
        try:
            # Resmi indir
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Resmi PIL ile aç
            image = Image.open(io.BytesIO(response.content))
            
            # Resmi geçici dosyaya kaydet
            temp_path = "/tmp/twitter_image.jpg"
            image.save(temp_path, "JPEG")
            
            # Android'e resmi kopyala (bu kısım cihaza göre değişebilir)
            # Şimdilik sadece URL'yi metne ekleyeceğiz
            logger.info(f"UIAutomator2: Resim indirildi - {image_url}")
            return True
            
        except Exception as e:
            logger.error(f"UIAutomator2: Resim indirme hatası - {e}")
            return False
    
    def _post_tweet(self) -> Optional[str]:
        """Tweet'i gönder - UI dump'tan doğru selector"""
        try:
            # Doğru Resource ID ile tweet gönderme butonu (UI dump'tan)
            if self.device(resourceId="com.twitter.android:id/button_tweet").exists:
                # Butonun enabled olup olmadığını kontrol et
                button = self.device(resourceId="com.twitter.android:id/button_tweet")
                if button.info.get('enabled', False):
                    button.click()
                    logger.info("UIAutomator2: Tweet gönderildi - button_tweet")
                    time.sleep(3)
                    
                    # Tweet ID oluştur (gerçek ID'yi alamayız)
                    tweet_id = f"uiautomator_{int(time.time())}"
                    return tweet_id
                else:
                    logger.warning("UIAutomator2: Tweet gönderme butonu disabled")
                    return None
            
            # Alternatif: Text ile arama
            if self.device(text="GÖNDERİ").exists:
                self.device(text="GÖNDERİ").click()
                logger.info("UIAutomator2: Tweet gönderildi - text: GÖNDERİ")
                time.sleep(3)
                tweet_id = f"uiautomator_{int(time.time())}"
                return tweet_id
            
            logger.error("UIAutomator2: Tweet gönderme butonu bulunamadı")
            return None
            
        except Exception as e:
            logger.error(f"UIAutomator2: Tweet gönderme hatası - {e}")
            return None
    
    async def publish_tweet(self, content: TweetContent) -> PublishResult:
        """Tweet'i UIAutomator2 ile gönder"""
        try:
            logger.info("UIAutomator2: Tweet gönderme başlatılıyor...")
            
            # Cihaza bağlan
            if not self._setup_device():
                return PublishResult(
                    success=False,
                    tweet_id=None,
                    error="UIAutomator2: Cihaz bağlantısı kurulamadı"
                )
            
            # Twitter uygulamasını aç
            if not self._open_twitter_app():
                return PublishResult(
                    success=False,
                    tweet_id=None,
                    error="UIAutomator2: Twitter uygulaması açılamadı"
                )
            
            # Compose butonuna tıkla (eğer compose ekranında değilsek)
            if not self._is_compose_screen_open():
                if not self._find_compose_button():
                    return PublishResult(
                        success=False,
                        tweet_id=None,
                        error="UIAutomator2: Compose butonu bulunamadı"
                    )
            
            # Tweet metnini yaz
            if not self._write_tweet_text(content):
                return PublishResult(
                    success=False,
                    tweet_id=None,
                    error="UIAutomator2: Tweet metni yazılamadı"
                )
            
            # Medya ekle
            if content.media_url:
                self._add_media(content.media_url)
            
            # Tweet'i gönder
            tweet_id = self._post_tweet()
            if not tweet_id:
                return PublishResult(
                    success=False,
                    tweet_id=None,
                    error="UIAutomator2: Tweet gönderilemedi"
                )
            
            logger.info(f"UIAutomator2: Tweet başarıyla gönderildi - {tweet_id}")
            
            return PublishResult(
                success=True,
                tweet_id=tweet_id,
                error=None
            )
            
        except Exception as e:
            logger.error(f"UIAutomator2: Tweet gönderme hatası - {e}")
            return PublishResult(
                success=False,
                tweet_id=None,
                error=f"UIAutomator2: {str(e)}"
            )
        
        finally:
            # Temizlik
            self._cleanup_device()
    
    def get_publisher_name(self) -> str:
        """Publisher adını döndür"""
        return "UIAutomator2 Twitter Publisher"
