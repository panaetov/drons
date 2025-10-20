import numpy as np
from scipy.optimize import least_squares
from pyproj import Transformer, CRS


def tdoa_localization_geodetic(
    receiver_latlons,
    time_differences,
    signal_speed=299792458.0,
    initial_guess_latlon=None
):
    """
    Локализация источника по TDoA с использованием географических координат.

    Параметры:
    - receiver_latlons: список или массив формы (N, 2) — [(lat0, lon0), (lat1, lon1), ...]
    - time_differences: np.array длины (N-1) — разности времени относительно первого приёмника
    - signal_speed: скорость сигнала (м/с), по умолчанию — скорость света
    - initial_guess_latlon: [lat, lon] — начальное приближение (опционально)

    Возвращает:
    - [lat, lon] — оценка позиции источника в градусах
    """
    receiver_latlons = np.asarray(receiver_latlons)
    N = receiver_latlons.shape[0]
    if len(time_differences) != N - 1:
        raise ValueError("time_differences must have length N-1")

    # === Шаг 1: Выбираем точку отсчёта для локальной проекции ===
    # Используем центр приёмников как origin
    origin_lat = np.mean(receiver_latlons[:, 0])
    origin_lon = np.mean(receiver_latlons[:, 1])

    # Создаём трансформер: из WGS84 (lat/lon) в локальную ENU (метры)
    # Используем проекцию "Orthographic" или "Azimuthal Equidistant" для небольших зон
    crs_wgs84 = CRS("EPSG:4326")
    crs_local = CRS(proj="aeqd", lat_0=origin_lat, lon_0=origin_lon, x_0=0, y_0=0, units="m")

    transformer = Transformer.from_crs(crs_wgs84, crs_local, always_xy=True)

    # Преобразуем приёмники в метры
    receiver_positions_m = np.array([
        transformer.transform(lon, lat) for lat, lon in receiver_latlons
    ])  # (N, 2) — [x, y] в метрах

    # Преобразуем начальное приближение (если есть)
    if initial_guess_latlon is not None:
        init_x, init_y = transformer.transform(
            initial_guess_latlon[1], initial_guess_latlon[0]
        )
        initial_guess_m = np.array([init_x, init_y])
    else:
        initial_guess_m = np.mean(receiver_positions_m, axis=0)

    # === Шаг 2: Выполняем TDoA в метрах ===
    delta_d = signal_speed * np.asarray(time_differences)

    r0 = receiver_positions_m[0]

    def residuals(pos):
        pos = np.asarray(pos)
        d0 = np.linalg.norm(pos - r0)
        errors = []
        for i in range(1, N):
            di = np.linalg.norm(pos - receiver_positions_m[i])
            predicted_delta = di - d0
            errors.append(predicted_delta - delta_d[i - 1])
        return errors

    result = least_squares(residuals, initial_guess_m, method='lm')
    estimated_x, estimated_y = result.x

    # === Шаг 3: Обратное преобразование в lat/lon ===
    inv_transformer = Transformer.from_crs(crs_local, crs_wgs84, always_xy=True)
    estimated_lon, estimated_lat = inv_transformer.transform(estimated_x, estimated_y)

    return np.array([estimated_lat, estimated_lon])


if __name__ == '__main__':
    # Координаты приёмников (Москва, ~1 км друг от друга)
    receivers = [
        [55.751244, 37.618423],  # R0
        [55.759000, 37.618423],  # R1 — ~860 м севернее
        [55.751244, 37.630000],  # R2 — ~800 м восточнее
    ]

    # Истинная позиция маячка
    true_latlon = [55.755, 37.625]

    # Симуляция времён (в реальности — измеряются)
    c = 299_792_458.0
    distances = []
    for lat, lon in receivers:
        from geopy.distance import geodesic
        d = geodesic((lat, lon), true_latlon).meters
        distances.append(d)

    times = np.array(distances) / c
    tdoa = times[1:] - times[0]  # относительно R0

    # Добавим немного шума
    tdoa_noisy = tdoa + np.random.normal(0, 1e-9, size=tdoa.shape)

    # Локализация
    estimated = tdoa_localization_geodetic(
        receiver_latlons=receivers,
        time_differences=tdoa_noisy,
        signal_speed=c
    )

    print(f"Истинная позиция: {true_latlon[0]:.6f}, {true_latlon[1]:.6f}")
    print(f"Оценка TDoA:      {estimated[0]:.6f}, {estimated[1]:.6f}")

    # Ошибка в метрах
    from geopy.distance import geodesic
    error_m = geodesic(true_latlon, estimated).meters
    print(f"Ошибка: {error_m:.2f} м")
