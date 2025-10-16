from datetime import (
    date,
    datetime,
)
from decimal import Decimal
from typing import Optional
from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.infrastructure.configs.db.models.base import Base
from src.infrastructure.configs.db.models.enums import (
    BookingStatusEnum,
    GenderEnum,
    PaymentMethodEnum,
    PaymentStatusEnum,
    TripStatusEnum,
)
from src.infrastructure.configs.db.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    """Пользователи системы (водители и пассажиры)"""

    __tablename__ = 'users'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, comment='Идентификатор пользователя'
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment='Email'
    )
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, comment='Номер телефона'
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False, comment='Пароль')
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, comment='Имя')
    last_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment='Фамилия'
    )
    birth_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment='Дата рождения'
    )
    gender: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Пол (1 - мужской, 2 - женский, 3 - другой)'
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment='URL аватара'
    )
    bio: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment='Описание профиля'
    )
    languages: Mapped[Optional[list[str]]] = mapped_column(
        JSON, nullable=True, comment='Языки общения'
    )

    rating: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal(0.00), comment='Рейтинг'
    )
    total_trips_as_driver: Mapped[int] = mapped_column(
        Integer, default=0, comment='Количество поездок водителем'
    )
    total_trips_as_passenger: Mapped[int] = mapped_column(
        Integer, default=0, comment='Количество поездок пассажиром'
    )

    is_driver: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment='Водитель'
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment='Активен'
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment='Верификация'
    )

    # Отношения
    driver_profile: Mapped['DriverProfile'] = relationship(
        'DriverProfile',
        back_populates='user',
        uselist=False,  # один-к-одному
    )
    vehicles: Mapped[list['Vehicle']] = relationship(back_populates='user')
    sent_messages: Mapped[list['Message']] = relationship(
        'Message', foreign_keys='Message.sender_id', back_populates='sender'
    )
    received_messages: Mapped[list['Message']] = relationship(
        'Message', foreign_keys='Message.receiver_id', back_populates='receiver'
    )
    trips_as_driver: Mapped[list['Trip']] = relationship(
        'Trip', foreign_keys='Trip.driver_id', back_populates='driver'
    )
    bookings_as_passenger: Mapped[list['Booking']] = relationship(
        'Booking', foreign_keys='Booking.passenger_id', back_populates='passenger'
    )
    reviews: Mapped[list['Review']] = relationship(
        'Review', foreign_keys='Review.reviewee_id', back_populates='reviewee'
    )

    @property
    def gender_enum(self) -> Optional[GenderEnum]:
        return GenderEnum(self.gender) if self.gender else None

    @gender_enum.setter
    def gender_enum(self, value: GenderEnum):
        self.gender = value.value if value else None


class DriverProfile(Base, TimestampMixin):
    """Профили водителей с дополнительной информацией"""

    __tablename__ = 'driver_profiles'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, comment='Идентификатор водителя'
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), nullable=False, comment='Идентификатор пользователя'
    )

    # Отношения
    user: Mapped['User'] = relationship(back_populates='driver_profile')
    vehicles: Mapped[list['Vehicle']] = relationship(back_populates='driver_profile')


class Vehicle(Base, TimestampMixin):
    """Транспортные средства"""

    __tablename__ = 'vehicles'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, comment='Идентификатор транспортного средства'
    )
    driver_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey('driver_profiles.id'),
        nullable=False,
        comment='Идентификатор водителя',
    )

    make: Mapped[str] = mapped_column(
        String(100), nullable=False, comment='Марка автомобиля'
    )
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, comment='Модель автомобиля'
    )
    color: Mapped[str] = mapped_column(
        String(100), nullable=False, comment='Цвет автомобиля'
    )
    year: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Год выпуска автомобиля'
    )
    license_plate: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, comment='Номер автомобиля'
    )

    total_seats: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Общее количество мест'
    )
    comfort_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment='Уровень комфорта (1 — Обычный, 2 — Комфортный, 3 — Премиум)',
    )

    # Отношения
    driver_profile: Mapped['DriverProfile'] = relationship(back_populates='vehicles')
    trips: Mapped[list['Trip']] = relationship(back_populates='vehicle')


class City(Base, TimestampMixin):
    """Города для маршрутов"""

    __tablename__ = 'cities'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment='Идентификатор города'
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment='Название города'
    )
    country: Mapped[str] = mapped_column(String(100), nullable=False, comment='Страна')
    region: Mapped[str] = mapped_column(
        String(100), nullable=True, comment='Регион/область'
    )
    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6), nullable=False, comment='Широта'
    )
    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6), nullable=False, comment='Долгота'
    )
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, comment='Часовой пояс'
    )

    # Отношения
    departure_routes: Mapped[list['Route']] = relationship(
        'Route', foreign_keys='Route.departure_city_id', back_populates='departure_city'
    )
    arrival_routes: Mapped[list['Route']] = relationship(
        'Route', foreign_keys='Route.arrival_city_id', back_populates='arrival_city'
    )


class Route(Base, TimestampMixin):
    """Маршруты между городами"""

    __tablename__ = 'routes'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment='Идентификатор маршрута'
    )
    departure_city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cities.id'),
        nullable=False,
        comment='Идентификатор города отправления',
    )
    arrival_city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cities.id'),
        nullable=False,
        comment='Идентификатор города прибытия',
    )
    distance_km: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Расстояние в километрах'
    )
    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Ориентировочное время в пути (минуты)'
    )
    trips_count: Mapped[int] = mapped_column(
        Integer, default=0, comment='Количество поездок по маршруту'
    )

    # Отношения
    departure_city: Mapped['City'] = relationship(
        'City', foreign_keys=[departure_city_id], back_populates='departure_routes'
    )
    arrival_city: Mapped['City'] = relationship(
        'City', foreign_keys=[arrival_city_id], back_populates='arrival_routes'
    )
    trips: Mapped[list['Trip']] = relationship(back_populates='route')


class Trip(Base, TimestampMixin):
    """Поездки"""

    __tablename__ = 'trips'

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment='Идентификатор поездки'
    )
    driver_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), nullable=False, comment='Идентификатор водителя'
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        ForeignKey('vehicles.id'),
        nullable=False,
        comment='Идентификатор транспортного средства',
    )
    route_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('routes.id'),
        nullable=False,
        comment='Идентификатор маршрута',
    )
    available_seats: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Количество доступных мест'
    )
    price_per_seat: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment='Цена за место'
    )
    intermediate_stops: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment='Промежуточные остановки (JSON)'
    )
    currency: Mapped[str] = mapped_column(String(3), default='RUB', comment='Валюта')
    status: Mapped[int] = mapped_column(
        Integer,
        default=TripStatusEnum.PLANNED.value,
        comment='Статус поездки (1-запланирована, 2-подтверждена, 3-в пути, 4-завершена, 5-отменена)',
    )
    auto_accept_bookings: Mapped[bool] = mapped_column(
        Boolean, default=False, comment='Автоматическое подтверждение бронирований'
    )
    smoking_allowed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment='Разрешено ли курение'
    )
    pets_allowed: Mapped[bool] = mapped_column(
        Boolean, default=False, comment='Разрешены ли животные'
    )
    max_two_passengers_back: Mapped[bool] = mapped_column(
        Boolean, default=False, comment='Максимум 2 пассажира сзади'
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment='Описание поездки'
    )

    # Отношения
    driver: Mapped['User'] = relationship(
        'User', foreign_keys=[driver_id], back_populates='trips_as_driver'
    )
    vehicle: Mapped['Vehicle'] = relationship(back_populates='trips')
    route: Mapped['Route'] = relationship(back_populates='trips')
    bookings: Mapped[list['Booking']] = relationship(back_populates='trip')
    messages: Mapped[list['Message']] = relationship(back_populates='trip')
    reviews: Mapped[list['Review']] = relationship(back_populates='trip')


class Message(Base, TimestampMixin):
    """Сообщения между пользователями"""

    __tablename__ = 'messages'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, comment='Идентификатор сообщения'
    )
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('trips.id'), nullable=False, comment='Идентификатор поездки'
    )
    sender_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), nullable=False, comment='Идентификатор отправителя'
    )
    receiver_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), nullable=False, comment='Идентификатор получателя'
    )
    message_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment='Содержание сообщения'
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment='Прочитано'
    )

    # Отношения
    trip: Mapped['Trip'] = relationship(back_populates='messages')
    sender: Mapped['User'] = relationship(
        'User', foreign_keys=[sender_id], back_populates='sent_messages'
    )
    receiver: Mapped['User'] = relationship(
        'User', foreign_keys=[receiver_id], back_populates='received_messages'
    )


class Booking(Base, TimestampMixin):
    """Бронирования поездок"""

    __tablename__ = 'bookings'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment='Идентификатор бронирования',
    )
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('trips.id'), nullable=False, comment='Идентификатор поездки'
    )
    passenger_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), nullable=False, comment='Идентификатор пассажира'
    )
    seats_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment='Количество забронированных мест'
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment='Общая стоимость'
    )
    status: Mapped[int] = mapped_column(
        Integer, default=BookingStatusEnum.PENDING.value, comment='Статус бронирования'
    )

    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment='Причина отмены'
    )

    # Отношения
    trip: Mapped['Trip'] = relationship(back_populates='bookings')
    passenger: Mapped['User'] = relationship(
        'User', foreign_keys=[passenger_id], back_populates='bookings_as_passenger'
    )
    payments: Mapped[list['Payment']] = relationship(back_populates='booking')

    @property
    def status_enum(self) -> BookingStatusEnum:
        return BookingStatusEnum(self.status)

    @status_enum.setter
    def status_enum(self, value: BookingStatusEnum) -> None:
        self.status = value.value


class Review(Base, TimestampMixin):
    """Отзывы и рейтинги"""

    __tablename__ = 'reviews'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, comment='Идентификатор отзыва'
    )
    trip_id: Mapped[int] = mapped_column(
        ForeignKey('trips.id'), nullable=False, comment='Идентификатор поездки'
    )
    reviewer_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'), nullable=False, comment='Идентификатор автора отзыва'
    )
    reviewee_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id'),
        nullable=False,
        comment='Идентификатор получателя отзыва',
    )
    rating: Mapped[int] = mapped_column(
        Integer, nullable=False, comment='Общая оценка (1-5)'
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment='Текст отзыва'
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, default=True, comment='Видимость отзыва'
    )

    # Отношения
    trip: Mapped['Trip'] = relationship(back_populates='reviews')
    reviewer: Mapped['User'] = relationship('User', foreign_keys=[reviewer_id])
    reviewee: Mapped['User'] = relationship('User', foreign_keys=[reviewee_id])


class Payment(Base, TimestampMixin):
    """Платежи"""

    __tablename__ = 'payments'

    id: Mapped[UUID] = mapped_column(
        primary_key=True, default=uuid4, comment='Идентификатор платежа'
    )
    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('bookings.id'),
        nullable=False,
        comment='Идентификатор бронирования',
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment='Сумма платежа'
    )
    currency: Mapped[str] = mapped_column(String(3), default='RUB', comment='Валюта')
    platform_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment='Комиссия платформы'
    )
    driver_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, comment='Сумма к выплате водителю'
    )
    payment_method: Mapped[int] = mapped_column(
        Integer,
        default=PaymentMethodEnum.CARD.value,
        nullable=False,
        comment='Способ оплаты',
    )
    payment_provider: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment='Провайдер платежей'
    )
    external_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment='Внешний ID платежа'
    )
    status: Mapped[int] = mapped_column(
        Integer, default=PaymentStatusEnum.PENDING.value, comment='Статус платежа'
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment='Время обработки платежа'
    )
