import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import aioschedule
from aiogram import Bot
from logger import logger
from helper import resolve_message_text, send_telegram_message


class NotificationScheduler:
    """Класс для управления отложенными уведомлениями"""
    
    def __init__(self, bot: Bot, notifications_file: str = "notifications_sample.json"):
        self.bot = bot
        self.notifications_file = notifications_file
        self.sent_notifications = set()  # Для отслеживания отправленных уведомлений (дедупликация на цикл)
    
    def load_notifications(self) -> List[Dict]:
        """Загрузка списка уведомлений из JSON файла (формат списка объектов)."""
        try:
            with open(self.notifications_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # В notifications_sample.json корневой тип — список
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get('notifications', [])
                return []
        except FileNotFoundError:
            logger.warning(f"Файл {self.notifications_file} не найден")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []
    
    async def send_notification(self, telegram_id: int, text: str, notification_id: str, max_attempts: int) -> Tuple[str, Optional[str], int]:
        """Отправка одного уведомления через вспомогательную функцию с ретраями."""
        if notification_id in self.sent_notifications:
            return "skipped", None, 0
        status, error_text, attempts_used = await send_telegram_message(
            bot=self.bot,
            telegram_id=telegram_id,
            message=text,
            max_attempts=max_attempts,
        )
        if status == "sent":
            self.sent_notifications.add(notification_id)
            logger.info(f"Отправлено уведомление {notification_id} пользователю {telegram_id}")
        else:
            logger.error(f"Ошибка отправки уведомления {notification_id} пользователю {telegram_id}: {error_text}")
        return status, error_text, attempts_used
    
    async def process_pending_notifications(self):
        """Обработка всех запланированных уведомлений из notifications_sample.json по правилам ТЗ."""
        notifications = self.load_notifications()
        now_utc = datetime.now(timezone.utc)

        for item in notifications:
            try:
                # 1) Статус
                status_value = item.get('status')
                if status_value != 'pending':
                    continue

                # 2) Время отправки
                scheduled_at_str = item.get('scheduled_at')
                try:
                    # Поддержка суффикса 'Z' и смещений
                    if scheduled_at_str.endswith('Z'):
                        scheduled_at = datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
                    else:
                        scheduled_at = datetime.fromisoformat(scheduled_at_str)
                    if scheduled_at.tzinfo is None:
                        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
                except (ValueError, AttributeError) as e:
                    logger.error(f"❌ Ошибка парсинга scheduled_at '{scheduled_at_str}': {e}")
                    continue

                if now_utc < scheduled_at:
                    continue

                # 3) Резолв текста
                message_marker = item.get('message')
                resolved_text = resolve_message_text(message_marker)
                if not resolved_text:
                    logger.warning(f"⚠️ Не удалось резолвить текст по маркеру '{message_marker}'")
                    # Формируем обновлённый объект как пример (ошибка)
                    updated = {
                        **item,
                        'status': 'failed',
                        'error': f"unknown_message_marker:{message_marker}",
                        'attempts': item.get('attempts', 0) + 1,
                        'message': message_marker,
                        'scheduled_at': scheduled_at_str,
                    }
                    logger.info(f"UPDATED_OBJECT: {json.dumps(updated, ensure_ascii=False)}")
                    continue

                # 4) Отправка
                telegram_id = item.get('telegram_id')
                max_attempts = item.get('max_attempts', 3)
                notification_id = str(item.get('id', item.get('dedup_key', f"{telegram_id}:{scheduled_at_str}")))
                send_status, error_text, attempts_used = await self.send_notification(
                    telegram_id=telegram_id,
                    text=resolved_text,
                    notification_id=notification_id,
                    max_attempts=max_attempts,
                )

                # 5) Формируем обновлённый объект и логируем
                updated = {
                    **item,
                    'status': 'sent' if send_status == 'sent' else 'failed',
                    'error': error_text,
                    'attempts': item.get('attempts', 0) + attempts_used,
                    'message': resolved_text,
                    'scheduled_at': scheduled_at_str,
                    'sent_at': now_utc.isoformat(),
                }
                logger.info(f"UPDATED_OBJECT: {json.dumps(updated, ensure_ascii=False)}")

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