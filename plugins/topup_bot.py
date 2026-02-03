from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from playwright.sync_api import sync_playwright

# Импортируем типы для подсказок (для удобства разработки)
if TYPE_CHECKING:
    from cardinal import Cardinal
    from objects import Order

logger = logging.getLogger("Cardinal.TopUpPlugin")


def init_plugin(cardinal: Cardinal):
    """
    Функция инициализации, которую Cardinal вызывает при запуске.
    """
    # Регистрируем обработчик события нового заказа
    cardinal.event_manager.register_handler("new_order", handle_new_order)
    logger.info("Плагин авто-пополнения успешно загружен!")


def handle_new_order(cardinal: Cardinal, order: Order):
    """
    Вызывается, когда появляется новый заказ.
    """
    # 1. Проверяем, что это нужный нам товар (по названию или категории)
    if "Пополнение" not in order.title:
        return

    logger.info(f"Новый заказ {order.id}! Начинаю обработку...")

    # 2. Получаем данные из чата или описания
    # Часто покупатели пишут данные в чат. cardinal.get_chat_history(order.id)
    # Или используем order.description, если данные в форме заказа.

    player_id = "12345678"  # Тут должна быть логика парсинга из текста

    # 3. Запускаем пополнение
    success = run_browser_automation(player_id, order.amount)

    if success:
        cardinal.send_message(order.id, "Ваш заказ успешно выполнен!")
    else:
        cardinal.send_message(order.id, "Произошла ошибка при пополнении. Скоро подойдет оператор.")


def run_browser_automation(player_id, amount):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Скрытый режим
            page = browser.new_page()
            page.goto('https://official-game-topup.com')

            # 1. Ввод ID игрока
            page.fill('input#user_id', player_id)
            page.click('button#check_user')
            page.wait_for_timeout(2000)  # Ждем проверки ника

            # 2. Выбор товара (нужна логика сопоставления суммы заказа и кнопки)
            page.click(f"text='{amount} Diamonds'")

            # 3. Оплата
            # Тут самое сложное: автоматизация кошелька или карты.
            # Если на сайте есть баланс вашего личного кабинета — это проще всего.
            page.click('button#pay_from_balance')

            browser.close()
            return True
    except Exception as e:
        logger.error(f"Ошибка автоматизации: {e}")
        return False
