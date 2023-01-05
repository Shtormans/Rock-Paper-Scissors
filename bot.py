from datetime import datetime
import random
import config
from aiogram import Bot, Dispatcher, executor, types

bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

games = {}


async def remove_game(game_id):
    del games[game_id]
    chat_id = game_id[:game_id.find(" ")]
    message_id = game_id[game_id.find(" ")+1:]
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text="No response for a long time. Deleted", reply_markup=None)


async def check_games():
    time_now = datetime.now()
    for game in games.copy().items():
        if (time_now - game[1][0]).total_seconds() > 60 * 2:
            await remove_game(game[0])


async def get_winner(first, second):
    if first == "Rock":
        if second == "Rock":
            return "tie"
        if second == "Paper":
            return "second"
        if second == "Scissors":
            return "first"
    elif first == "Paper":
        if second == "Rock":
            return "first"
        if second == "Paper":
            return "tie"
        if second == "Scissors":
            return "second"
    else:
        if second == "Rock":
            return "second"
        if second == "Paper":
            return "first"
        if second == "Scissors":
            return "tie"


@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    answer = "Hello! I am Rock Paper Scissors Bot"
    answer += "\nTo play - just reply to my message with command /playrps"
    await message.answer(answer)


@dp.message_handler(commands=['playRPS'])
async def start_game(message: types.Message):
    if message.reply_to_message == None:
        await message.answer("Reply to another person's message with command /playrps")
        return

    reply_user = message.reply_to_message.from_user.first_name

    markup = types.InlineKeyboardMarkup()
    button1 = types.InlineKeyboardButton("Rock", callback_data="Rock")
    button2 = types.InlineKeyboardButton("Paper", callback_data="Paper")
    button3 = types.InlineKeyboardButton("Scissors", callback_data="Scissors")
    markup.add(button1, button2, button3)

    answer = "Game starts"
    answer += "\n" + message.from_user.first_name + ": ❎"

    bot_me = await bot.get_me()
    if reply_user == bot_me.first_name:
        random_button = random.choice([button1.callback_data, button2.callback_data, button3.callback_data])
        answer += "\n" + reply_user + ": ✅"
    else:
        answer += "\n" + reply_user + ": ❎"

    game_message = await message.answer(answer, reply_markup=markup)

    await check_games()
    games[f"{game_message.chat.id} {game_message.message_id}"] = [datetime.now()]

    if reply_user == bot_me.first_name:
        games[f"{game_message.chat.id} {game_message.message_id}"].append(random_button)


@dp.callback_query_handler()
async def process_callback(callback_query: types.CallbackQuery):
    message = callback_query.message
    message_text = message.text

    user_name = callback_query.from_user.first_name
    if message_text[message_text.find(user_name) + len(user_name) + 2] == "✅":
        await callback_query.answer("You've already pressed " +
                                    games[str(message.chat.id) + " " + str(message.message_id)][1])
        return
    elif callback_query.from_user.first_name not in message_text:
        await callback_query.answer("You are not playing right now")
        return

    if user_name in message_text:
        if "✅" in message_text:
            first_user_answer = games[f"{message.chat.id} {message.message_id}"][1]
            first_user = message_text[message_text.find("\n")+1:message_text.find(":")]
            second_user = message_text[message_text.rfind("\n")+1:message_text.rfind(":")]

            if first_user == callback_query.from_user.first_name:
                result = await get_winner(callback_query.data, first_user_answer)
            else:
                result = await get_winner(first_user_answer, callback_query.data)

            answer = "Game ends. Results:"
            answer += "\n" + first_user + ": "
            if first_user == user_name:
                answer += callback_query.data
                answer += "\n" + second_user + ": " + first_user_answer
            else:
                answer += first_user_answer
                answer += "\n" + user_name + ": " + callback_query.data
            answer += "\n"

            if result == "tie":
                answer += "Tie"
            elif result == "first":
                answer += first_user + " WINS"
            else:
                answer += second_user + " WINS"

            await message.edit_text(answer, reply_markup=None)
            del games[f"{message.chat.id} {message.message_id}"]
        else:
            index = message_text.find(user_name) + len(user_name)
            message_text = message_text[:index+2] + "✅" + message_text[index+3:]
            games[f"{message.chat.id} {message.message_id}"].append(callback_query.data)
            await message.edit_text(message_text, reply_markup=message.reply_markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
