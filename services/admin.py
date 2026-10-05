"""Админка провайдеров: модели и API-ключи.
Запуск: python services/admin.py
Бот подхватывает изменения без перезапуска."""
import asyncio
import getpass

try:
    import llm_storage                      # запуск как python services/admin.py
except ImportError:
    from services import llm_storage        # запуск как python -m services.admin


def mask(key: str) -> str:
    return key[:6] + "…" + key[-4:] if len(key) > 12 else "***"


async def main():
    await llm_storage.init_llm_db()
    while True:
        print("\n===== АДМИНКА =====")
        print("1) Список моделей    2) Добавить модель   3) Выключить модель")
        print("4) Список ключей     5) Добавить ключ     6) Выключить ключ")
        print("0) Выход")
        choice = input("> ").strip()

        if choice == "1":
            for m in await llm_storage.get_models_all():
                st = "active" if m["is_active"] else "OFF"
                print(f"  [{m['id']}] {m['name']} | {m['provider']}/{m['api_name']} | {st}")
        elif choice == "2":
            name = input("Название в меню: ").strip()
            api_name = input("API-имя (gpt-4o-mini): ").strip()
            provider = input("Провайдер [openai]: ").strip() or "openai"
            if name and api_name:
                print(f"✅ Модель добавлена, id={await llm_storage.add_model(name, api_name, provider)}")
        elif choice == "3":
            await llm_storage.set_model_active(int(input("id модели: ")), False)
            print("🚫 Модель выключена")
        elif choice == "4":
            for k in await llm_storage.get_api_keys_all():
                st = "active" if k["is_active"] else "OFF"
                print(f"  [{k['id']}] {k['provider']} | {mask(k['key'])} | {st}")
        elif choice == "5":
            provider = input("Провайдер (openai/anthropic): ").strip()
            key = getpass.getpass("API-ключ (не виден при вводе): ").strip()
            if provider and key:
                print(f"✅ Ключ добавлен, id={await llm_storage.add_api_key(provider, key)}")
        elif choice == "6":
            await llm_storage.set_api_key_active(int(input("id ключа: ")), False)
            print("🚫 Ключ выключен")
        elif choice == "0":
            break

asyncio.run(main())