"""Распределение нагрузки по API-ключам.

ПОКА ЗАГЛУШКА. Потом тут будет:
- round-robin по пулу get_api_keys(provider)
- при 429/лимите: fails += 1 и следующий ключ
- восстановление ключа, когда лимит сбросился

Бот сюда напрямую не лезет — спрашивает готовый ключ.
"""
from services import llm_storage


async def acquire_key(provider: str):
    """Временно: первый активный ключ. Ротация — позже."""
    keys = await llm_storage.get_api_keys(provider)
    if not keys:
        raise RuntimeError(f"Нет активных ключей для провайдера {provider}")
    return keys[0]