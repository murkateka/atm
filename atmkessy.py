import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# --- Укажите токен вашего бота ---
TOKEN = '8497800419:AAGS8Xp01IWB8vnkaO17nSxh8ojl_Dxtoug'

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Admin and Operators ---
ADMIN_ID = 7113985137  # <-- вставьте сюда свой Telegram user_id
OPERATORS = set([ADMIN_ID])  # админ автоматически оператор

# --- Shared global data ---
total = 0.0
percent = 0.0
rate = 1.0
history = []
HISTORY_LIMIT = 5

deposit_usdt = 0.0

# ---------- Logic ----------
def add_payment(amount):
    global total, history
    total += amount
    history.append(amount)
    if len(history) > HISTORY_LIMIT:
        history.pop(0)


def reset_all():
    global total, percent, rate, history, deposit_usdt
    total = 0.0
    percent = 0.0
    rate = 1.0
    history.clear()
    deposit_usdt = 0.0


def generate_report():
    clean_total = total * (1 - percent / 100)
    usdt = clean_total / rate if rate else 0
    diff = deposit_usdt - usdt

    text = (
        f"ОБОРОТ:\n"
        f"Всего: {total:.2f} ₽\n"
        f"- {percent}%: {clean_total:.2f} ₽\n"
        f"USDT: {usdt:.2f}\n\n"
        f"Депозит: {deposit_usdt:.2f} USDT\n"
        f"Остаток депозита: {diff:.2f} USDT\n\n"
        f"Курс: {rate} ₽ | Процент: {percent}%\n\n"
        f"История (5):\n"
    )
    for i, h in enumerate(history, 1):
        text += f"{i}) {'+' if h >= 0 else ''}{h:.2f} ₽\n"
    return text

# ---------- Commands ----------

@dp.message(lambda m: m.text and m.text.lower().startswith('оператор'))
async def grant_operator(message: Message):
    # только админ может выдавать операторов
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Нет прав")
        return

    # reply-способ
    if message.reply_to_message:
        user = message.reply_to_message.from_user
        OPERATORS.add(user.id)
        await message.answer(f"✅ @{user.username or user.id} теперь оператор")
        return

    await message.answer(
        "Использование:\n"
        "• оператор (ответом на сообщение)"
    )

@dp.message(Command('start'))
async def start(message: Message):
    await message.answer(
        "Использование:\n"
        "• оператор (ответом на сообщение)"
    )

@dp.message(Command('operators'))
async def operators(message: Message):
    await message.answer("👥 Операторы:\n" + '\n'.join(map(str, OPERATORS)) if OPERATORS else "Операторов нет")

@dp.message(Command('resetall'))
async def reset_cmd(message: Message):
    if message.from_user.id not in OPERATORS:
        return
    reset_all()
    await message.answer("⚠️ Всё сброшено")

@dp.message(lambda m: m.from_user.id in OPERATORS and m.text)
async def handler(message: Message):
    t = message.text.lower().strip()
    try:
        if t.startswith('+') or t.startswith('-'):
            add_payment(float(t))
        elif t.startswith('курс'):
            global rate
            rate = float(t.split()[1])
        elif t.startswith('процент'):
            global percent
            percent = float(t.split()[1])
        elif t.startswith('депозит'):
            global deposit_usdt
            deposit_usdt += float(t.split()[1])
        elif t.startswith('вычесть'):
            deposit_usdt -= float(t.split()[1])
        else:
            return
        await message.answer(generate_report())
    except Exception:
        await message.answer("❌ Ошибка ввода")

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
