from enum import (
    Enum,
    IntEnum,
)


class GenderEnum(IntEnum):
    """Пол пользователя"""

    MALE = 1  # мужской
    FEMALE = 2  # женский
    OTHER = 3  # другой / не указан

    @property
    def display_name(self) -> str:
        return {
            self.MALE: 'Мужской',
            self.FEMALE: 'Женский',
            self.OTHER: 'Другой',
        }[self]


class TripStatusEnum(int, Enum):
    """Статус поездки"""

    PLANNED = 1  # запланирована
    CONFIRMED = 2  # подтверждена
    IN_PROGRESS = 3  # в пути / выполняется
    COMPLETED = 4  # завершена
    CANCELLED = 5  # отменена


class BookingStatusEnum(int, Enum):
    """Статус бронирования"""

    PENDING = 1  # ожидает подтверждения
    CONFIRMED = 2  # подтверждено
    PAID = 3  # оплачено
    COMPLETED = 4  # завершено
    CANCELLED_BY_PASSENGER = 5  # отменено пассажиром
    CANCELLED_BY_DRIVER = 6  # отменено водителем
    NO_SHOW = 7  # пассажир не явился


class PaymentStatusEnum(int, Enum):
    """Статус платежа"""

    PENDING = 1  # ожидает обработки
    PROCESSING = 2  # обрабатывается
    COMPLETED = 3  # успешно завершен
    FAILED = 4  # неудачный
    REFUNDED = 5  # возвращен полностью
    PARTIALLY_REFUNDED = 6  # возвращен частично


class PaymentMethodEnum(int, Enum):
    """Способ оплаты"""

    CARD = 1  # банковская карта
    WALLET = 2  # кошелек (внутренний баланс)
    CASH = 3  # наличные


class ComfortLevelEnum(int, Enum):
    """Уровень комфорта"""

    BASIC = 1  # базовый
    COMFORT = 2  # комфорт
    PREMIUM = 3  # премиум
