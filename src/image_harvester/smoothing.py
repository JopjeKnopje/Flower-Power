def ema(data: list[int], weight: float) -> list[float]:
    ema_data: list[float] = []
    ema_data.append(data[0])
    for p in data:
        ema = (weight * p) + (ema_data[-1] * (1 - weight))
        ema_data.append(ema)
    return ema_data


def sma(data: list[int], range: int) -> list[float]:
    sma_data: list[float] = []
    for i, _ in enumerate(data, start=1):
        if i < range:
            x = sum(data[0:i]) / i
        else:
            x = sum(data[i - range : i]) / range
        sma_data.append(x)
    return sma_data
