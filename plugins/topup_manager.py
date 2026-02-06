from __future__ import annotations
from typing import TYPE_CHECKING
import logging
import requests

# Базовые классы Cardinal (пути могут отличаться в зависимости от версии, проверьте cardinal.py)
from objects import Order
from abstract import Plugin

if TYPE_CHECKING:
    from cardinal import Cardinal


class TopUpPlugin(Plugin):
    def __init__(self, cardinal: Cardinal):
        super().__init__(cardinal)
        self.name = "AutoTopUp"
        self.description = "Автоматическое пополнение игр через внешнее API"

        # Настройки (в идеале вынести в config.yaml)
        self.api_key = "ВАШ_API_КЛЮЧ_ПОСТАВЩИКА"
        self.provider_url = "https://api.provider.com/v1/pay"
        self.target_category = "Пополнение Steam"  # Название категории для фильтрации

    def on_order_status_changed(self, order: Order, old_status: int):
        """
        Метод вызывается при изменении статуса заказа.
        Статус 1 обычно означает 'Оплачено'.
        """
        if order.status == 1 and old_status != 1:
            # Проверяем, наш ли это товар
            if self.target_category in order.title:
                logging.info(f"Обнаружен заказ {order.id} на пополнение. Начинаю обработку...")
                self.process_order(order)

    def extract_player_id(self, text: str) -> str | None:
        """
        Логика парсинга ID игрока (логина) из описания заказа или сообщения.
        """
        # Здесь можно использовать регулярные выражения (re)
        # Для примера просто берем текст заказа, если покупатель пишет логин в поле
        return text.strip()

    def process_order(self, order: Order):
        # 1. Получаем данные для пополнения
        # Можно взять из order.description или через запрос сообщений чата
        player_id = self.extract_player_id(order.description)

        if not player_id:
            self.cardinal.send_message(order.id, "Ошибка: Не удалось определить логин. Свяжитесь с продавцом.")
            return

        # 2. Формируем запрос к API поставщика
        payload = {
            "api_key": self.api_key,
            "account": player_id,
            "amount": order.price,  # Сумма, которую оплатил клиент
            "order_id": order.id  # Наш внутренний ID для отслеживания
        }

        try:
            response = requests.post(self.provider_url, json=payload, timeout=10)
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                logging.info(f"Заказ {order.id} успешно пополнен через API.")
                self.cardinal.send_message(order.id,
                                           f"Баланс {player_id} успешно пополнен. Пожалуйста, подтвердите заказ!")
            else:
                error_msg = result.get("error", "Неизвестная ошибка API")
                logging.error(f"Ошибка API для заказа {order.id}: {error_msg}")
                self.cardinal.send_message(order.id,
                                           "Произошла временная ошибка при пополнении. Мы скоро все исправим!")

        except Exception as e:
            logging.error(f"Критическая ошибка при обработке заказа {order.id}: {e}")

    def on_start(self):
        logging.info(f"Плагин {self.name} успешно запущен.")