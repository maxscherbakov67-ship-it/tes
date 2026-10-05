import asyncio
from database import storage

async def main():
    while True:
        print("\n1) Добавить модель  2) Список  3) Выключить модель  0) Выход")
        choice = input("> ").strip()

        if choice == "1":
            name = input("Название в меню: ").strip()
            api_name = input("API-имя (например gpt-4o-mini): ").strip()
            provider = input("Провайдер [openai]: ").strip() or "openai"
            if name and api_name:
                mid = await storage.add_model(name, api_name, provider)
                print(f"✅ Добавлена, id={mid}. Бот увидит её сразу, без перезапуска.")

        elif choice == "2":
            for m in await storage.get_models_all():
                state = "active" if m["is_active"] else "OFF"
                print(f"  [{m['id']}] {m['name']} | {m['provider']}/{m['api_name']} | {state}")

        elif choice == "3":
            mid = int(input("id модели: "))
            await storage.set_model_active(mid, False)
            print("🚫 Выключена")

        elif choice == "0":
            break

asyncio.run(main())