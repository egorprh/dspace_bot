import asyncio
import json
from datetime import datetime
from typing import List, Dict
import aioschedule
from aiogram import Bot
from logger import logger


class NotificationScheduler:
    """Класс для управления отложенными уведомлениями"""
    
    def __init__(self, bot: Bot, notifications_file: str = "files/notifications.json"):
        self.bot = bot
        self.notifications_file = notifications_file
        self.sent_notifications = set()  # Для отслеживания отправленных уведомлений
    
    def load_notifications(self) -> List[Dict]:
        """Загрузка списка уведомлений из JSON файла"""
        try:
            with open(self.notifications_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('notifications', [])
        except FileNotFoundError:
            logger.warning(f"Файл {self.notifications_file} не найден")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []
    
    async def send_notification(self, user_id: int, text: str, notification_id: str):
        """Отправка одного уведомления пользователю"""
        try:
            # Проверяем, не было ли уже отправлено это уведомление
            if notification_id in self.sent_notifications:
                return
            
            await self.bot.send_message(user_id, text, parse_mode="HTML")
            self.sent_notifications.add(notification_id)
            logger.info(f"Отправлено уведомление {notification_id} пользователю {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
    
    async def process_pending_notifications(self):
        """Обработка всех запланированных уведомлений"""
        notifications = self.load_notifications()
        current_time = datetime.now()
        
        for notification in notifications:
            try:
                # Получаем данные из уведомления с явной проверкой типов
                user_id = notification.get('user_id')
                text = notification.get('text')
                send_time_str = notification.get('send_time')
                # Проверяем наличие обязательных полей
                if not isinstance(user_id, int) or not isinstance(text, str) or not isinstance(send_time_str, str):
                    logger.warning(f"⚠️ Пропущено уведомление с неверными типами данных: {notification}")
                    continue
                
                # Генерируем ID уведомления
                notification_id = notification.get('id', f"{user_id}_{send_time_str}")
                if not isinstance(notification_id, str):
                    notification_id = str(notification_id)
                # Парсим время отправки (формат: 2025-10-04T12:00:00)
                try:
                    send_time = datetime.fromisoformat(send_time_str)
                except ValueError as e:
                    logger.error(f"❌ Ошибка парсинга времени '{send_time_str}': {e}")
                    continue
                
                                # Если время пришло и уведомление еще не отправлено
                if current_time >= send_time and notification_id not in self.sent_notifications:
                    # Теперь типы гарантированно корректны
                    await self.send_notification(user_id, text, notification_id)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка обработки уведомления: {e}")

    
    async def schedule_loop(self):
        """Основной цикл планировщика"""
        # Запускаем проверку каждые 30 секунд
        aioschedule.every(30).seconds.do(self.process_pending_notifications)
        
        logger.info("Планировщик уведомлений запущен")
        
        while True:
            await aioschedule.run_pending()
            await asyncio.sleep(1)


async def start_scheduler(bot: Bot):
    """Запуск планировщика в отдельной задаче"""
    scheduler = NotificationScheduler(bot)
    await scheduler.schedule_loop()