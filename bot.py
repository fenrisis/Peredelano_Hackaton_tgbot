import logging
import os
import config
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import db 
from profile_handlers import *
from profile_handlers import setup_handlers

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

class JoinTeamForm(StatesGroup):
    team_to_join = State()
    role_choice = State()

class InviteForm(StatesGroup):
    user_to_invite = State() 

class RemoveForm(StatesGroup):
    user_to_remove = State() 

async def on_startup(dp):
    await bot.set_webhook(config.URL_APP)


async def on_shutdown(dp):
    await bot.delete_webhook()

@dp.message_handler(Command("start"), chat_type=types.ChatType.PRIVATE)
async def send_welcome_private(message: types.Message):
    await message.reply(
        "Привет! Я бот-помощник Peredelano Hackaton.\n"
        "Заполните свой профиль [/profile]\n"
        "Документация.  [/documentation]\n",
        parse_mode="Markdown"
    )

@dp.message_handler(Command("documentation"), chat_type=types.ChatType.PRIVATE)
async def send_welcome_private(message: types.Message):
    welcome_text = (
        "Для начала работы с ботом, заполните свой профиль - /profile.\n"
        "Там нужно будет ввести вашу роль, опыт, ваш стек и короткую информацию о себе, "
        "идею (если она у вас есть, если нет, то так и напишите - нет), ссылку на ваш LinkedIn.\n\n"
        "После заполнения данных профиля, вас смогут найти капитаны других команд с помощью /hireforteam. "
        "И пригласить вас в команду с помощью  /invitetoteam. \n\n"
        "А ещё вы сможете найти уже существующие команды с помощью\n"
        " /findteam.\n"
        "Если вы хотите собрать свою команду, то вам нужно описать её с помощью\n"
        "/team.\n"
        "От вас потребуется ввести название команды, идею и требуемую роль (к сожалению, выбрать роль можно только одну).\n"
        "Позже вы сможете изменить требуемую роль на другую с помощью\n"
        "/editteam, но учтите, что меняя информацию о требуемой роли,\n"
        "вам придется заново ввести всю информацию по команде.\n"
        "Также вы можете описать требуемые роли в поле Идея.\n"
        "Посмотреть текущий состав команды, название,идею итд.\n"
        "/myteam. \n"
        "Из команды можно удалить участника с помощью /removefromteam и ему придёт уведомление.\n"
        "Вы можете уйти из команды с помощью команды  /leaveteam, но пожалуйста уведомите лидера. "
        "Распустить вашу команду можно с помощью   /deleteteam.\n\n"
        "Организатор: [@batyshka_Lenin]\n"
        "Разработчик бота: [@Leonid3]"
    )
    await message.reply(welcome_text, parse_mode="Markdown")


async def send_long_message(chat_id, text, max_size=4096):
    while text:
        # Отправка части текста не превышающей максимальный размер
        part = text[:max_size]
        await bot.send_message(chat_id, part)
        # Удаление отправленной части из текста
        text = text[len(part):]


@dp.message_handler(Command("findteam"))
async def find_team_command(message: Message):
    try:
        teams = db.get_all_teams_with_leaders()
        logging.info(f"Received teams from DB: {teams}")

        if not teams:
            await message.answer("Нет доступных команд.")
            return

        response = "Доступные команды:\n\n"
        for team in teams:
            response += (f"Название: {team['name']}\n"
                         f"Идея: {team['idea']}\n"
                         f"Требуемые роли: {team['required_roles']}\n"
                         f"Контакт лидера: {team['telegram_username']}\n\n")

        await send_long_message(message.chat.id, response)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз позже.")


@dp.message_handler(Command("leaveteam"), state=None)
async def leave_team(message: Message):
    user_id = message.from_user.id
    user_telegram_username = db.get_user_telegram_username(user_id)
    team_id = db.get_team_of_participant(user_id)

    # Проверяем, является ли пользователь лидером команды
    is_leader = db.check_team_exists(user_id)

    if not team_id:
        await message.answer("Вы не вступили в команду.")
        return

    # Если пользователь - лидер, запрещаем ему покидать команду
    if is_leader:
        await message.answer("Вы являетесь лидером команды и не можете покинуть её. "
                             "Вместо этого вы можете распустить команду с помощью команды /deleteteam.")
        return

    # Удаляем пользователя из команды
    db.remove_participant(user_id, team_id)
    await message.answer("Вы покинули команду.")
    
    # Получаем идентификатор пользователя лидера команды
    leader_id = db.get_team_leader_by_team_id(team_id)
    if leader_id and user_telegram_username:
        # Получаем telegram_username лидера команды
        leader_telegram_username = db.get_user_telegram_username(leader_id)
        if leader_telegram_username:
            # Отправляем сообщение лидеру команды(не работает:( )
            try:
                await bot.send_message(leader_telegram_username, f"Участник @{user_telegram_username} покинул вашу команду.")
            except Exception as e:
                
                logger.error(f"Ошибка при отправке сообщения: {e}")


@dp.message_handler(Command("invitetoteam"), state=None)
async def invite_to_team(message: Message):
    user_id = message.from_user.id

    # Проверка, является ли пользователь лидером какой-либо команды
    team = db.get_team_by_user_id(user_id)
    if not team:
        await message.answer("Вы не вступили в команду или вы не капитан в команде.")
        return

    # Получаем список всех пользователей
    users = db.get_all_users()  
    if not users:
        await message.answer("Нет доступных пользователей для приглашения.")
        return

    markup = InlineKeyboardMarkup()
    # Добавляем кнопку 'Отменить' в начало списка
    markup.add(InlineKeyboardButton('Отменить', callback_data='cancel_invite'))
    for user in users:
     display_name = user.get("telegram_username") or user.get("hackathon_username")
     if user['userId'] != user_id and not db.get_user_participation(user['userId']):
        markup.add(InlineKeyboardButton(display_name, callback_data=f"invite_{user['userId']}"))
            

    await message.answer("Выберите пользователя для приглашения в вашу команду:", reply_markup=markup)
    await InviteForm.user_to_invite.set()

# Обработчик для кнопки отмены в инлайн клавиатуре
@dp.callback_query_handler(text='cancel_invite', state=InviteForm.user_to_invite)
async def process_cancel_invite(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer("Приглашение отменено.")
    await state.finish()  # Завершаем текущее состояние
    await callback_query.message.edit_reply_markup()

@dp.callback_query_handler(lambda c: c.data.startswith("invite_"), state=InviteForm.user_to_invite)
async def invite_user_to_team_process(callback_query: CallbackQuery, state: FSMContext):
    user_id_to_invite = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id

    # Проверяем, является ли приглашаемый пользователь лидером какой-либо команды
    if db.check_team_exists(user_id_to_invite):
        await bot.send_message(callback_query.from_user.id, f"Пользователь, которого вы пытаетесь пригласить, уже является лидером другой команды.")
        await state.finish()
        return

    # Проверяем, является ли пользователь уже членом какой-либо команды
    existing_team_id = db.get_team_of_participant(user_id_to_invite)
    if existing_team_id:
        await bot.send_message(callback_query.from_user.id, f"Пользователь уже присоединился к другой команде.")
        await state.finish()
        return

    # Добавляем пользователя к команде как "Член команды"
    team_id = db.get_team_of_participant(user_id)  # Предполагаем, что текущий пользователь (капитан) является участником своей команды
    if not team_id:
        await bot.send_message(callback_query.from_user.id, "Произошла ошибка. Пожалуйста, попробуйте снова позже.")
        await state.finish()
        return
    
    db.add_participant(user_id_to_invite, team_id, "Член команды")

    # Уведомление приглашенному пользователю
    team = db.get_team_by_user_id(user_id)  # Получаем данные команды текущего пользователя
    team_name = team["name"] if "name" in team else "Команда"  
    await bot.send_message(user_id_to_invite, f"Вы были приглашены в {team_name}!\nЕсли вы не хотите в ней учавствовать\n[/leaveteam]")

    await bot.send_message(callback_query.from_user.id, f"Пользователь успешно приглашен в вашу команду!")
    await state.finish()


@dp.message_handler(Command("removefromteam"), state=None)
async def remove_from_team(message: Message):
    user_id = message.from_user.id
    logger.debug(f"Starting remove_from_team for user {user_id}")

    team = db.get_team_by_user_id(user_id)
    logger.debug(f"Team data for user {user_id}: {team}")

    if not team:
        await message.answer("Вы не вступили в команду или вы не капитан в команде.")
        return

    if 'teamId' not in team:
        logger.error(f"Key 'teamId' not found in team data for user {user_id}.")
        await message.answer("Ошибка: команда не найдена.")
        return

    team_members = db.get_team_members_by_team_id(team['teamId'])
    logger.debug(f"Team members for teamId {team['teamId']}: {team_members}")

    if not team_members or len(team_members) == 1:
        await message.answer("В вашей команде нет других членов.")
        return

    markup = InlineKeyboardMarkup()
    for member in team_members:
     if member['userId'] != user_id:
        display_name = member.get("telegram_username") or member.get("hackathon_username")
        markup.add(InlineKeyboardButton(display_name, callback_data=f"remove_{member['userId']}"))
    
    await message.answer("Выберите пользователя для удаления из вашей команды:", reply_markup=markup)
    await RemoveForm.user_to_remove.set()

@dp.callback_query_handler(lambda c: c.data.startswith("remove_"), state=RemoveForm.user_to_remove)
async def remove_user_from_team_process(callback_query: CallbackQuery, state: FSMContext):
    user_id_to_remove = int(callback_query.data.split("_")[1])
    user_id = callback_query.from_user.id
    logger.debug(f"Removing user {user_id_to_remove} from team of user {user_id}")

    team = db.get_team_by_user_id(user_id)
    if not team or 'teamId' not in team:
        logger.error(f"Team data error for user {user_id} when trying to remove {user_id_to_remove}")
        await bot.send_message(callback_query.from_user.id, f"Ошибка при удалении пользователя.")
        return

    team_id_to_remove_from = db.get_team_of_user(user_id_to_remove)
    members = db.get_team_members_by_team_id(team_id_to_remove_from)
    
    # Получаем информацию о пользователе, который покидает команду
    user_leaving = db.get_user_profile(user_id_to_remove) 
    user_name = user_leaving["telegram_username"] if "telegram_username" in user_leaving else "Пользователь"
    
    for member in members:
     if member["userId"] == user_id_to_remove:
        # Сообщение для пользователя, который был удалён
        await bot.send_message(member["userId"], "Вас удалили из команды.")
     else:
        # Сообщение для остальных членов команды
        await bot.send_message(member["userId"], f"{user_name} покинул команду!")

    db.remove_participant(user_id_to_remove, team["teamId"])
    await bot.send_message(callback_query.from_user.id, f"Пользователь успешно удален из вашей команды!")
    await state.finish()

@dp.message_handler(commands=['hireforteam'])
async def hire_for_team(message: types.Message):
    user_id = message.from_user.id
    
    # Проверка, является ли пользователь капитаном команды
    team = db.get_team_by_user_id(user_id)
    if not team:
        await message.answer("Вы не вступили в команду или вы не капитан в команде.")
        return

    # Извлечение всех пользователей
    users = db.get_all_users()

    # Формирование ответного сообщения
    response = "Пользователи для найма:\n\n"
    for user in users:
        # Проверка, является ли пользователь участником команды
        if not db.get_user_participation(user['userId']):
            # Использование hackathon_username если telegram_username отсутствует
            display_name = user.get('telegram_username') or user.get('hackathon_username')
            user_info = [
                f"Роль: {user['role']}",
                f"Опыт: {user['experience']}",
                f"Технологический стек: {user['tech_stack']}",
                f"Идея: {user['idea']}",
                f"LinkedIn профиль: {user['linkedin_profile']}",
                f"Имя пользователя: {display_name}"
            ]
            response += "\n".join(user_info) + "\n\n"

    # Отправка ответного сообщения
    await send_long_message(message.chat.id, response)


@dp.message_handler(Command("myteam"), state=None)
async def show_my_team(message: Message):
    user_id = message.from_user.id

    # Проверка, создан ли профиль пользователем
    user_exists = db.check_user_exists(user_id)
    if not user_exists:
        await message.answer("Вы еще не создали профиль. Пожалуйста, создайте профиль, чтобы просматривать команды.")
        return

    # Получение информации о команде, в которой состоит пользователь
    team_info = db.get_team_info_for_user(user_id)
    if not team_info:
        await message.answer("Вы не вступили в команду или вы не капитан в команде.")
        return
    
    # Формируем информацию о команде
    team_text = (
        f"Название команды: {team_info['name']}\n"
        f"Идея: {team_info['idea']}\n"
        f"Требуемые роли: {team_info['required_roles']}\n"
        f"Лидер команды: {team_info['leaderUsername']}\n\n"
        "Редактировать: [/editteam]."
    )
    
    # Получение данных о всех членах команды
    team_members_info = db.get_team_members_by_team_id(team_info['teamId'])
    team_members_text = "\n".join(
        [f"{member['telegram_username']} ({member['role']})" for member in team_members_info]
    ) if team_members_info else "Информация о членах команды недоступна."

    # Отправляем сообщение пользователю
    await message.answer(f"{team_text}\n\nУчастники команды:\n{team_members_text}")


confirmation_keyboard = InlineKeyboardMarkup().add(
    InlineKeyboardButton("Да", callback_data="delete_confirm_yes"),
    InlineKeyboardButton("Нет", callback_data="delete_confirm_no")
)

@dp.message_handler(Command("deleteteam"), state=None)
async def ask_delete_team(message: Message):
    user_id = message.from_user.id
    team = db.get_team_by_user_id(user_id)

    if not team:
        await message.answer("Вы не вступили в команду или вы не капитан в команде.")
        return

    await message.answer("Вы уверены, что хотите распустить вашу команду?", reply_markup=confirmation_keyboard)

@dp.callback_query_handler(lambda c: c.data == "delete_confirm_yes")
async def confirm_delete(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    team = db.get_team_by_user_id(user_id)
    team_members = db.get_team_members_by_team_id(team["teamId"])

   
    db.delete_team_and_participants(user_id, team["teamId"])

    for member in team_members:
        await bot.send_message(member["userId"], f"Команда '{team['name']}' была распущена лидером.")

    await bot.send_message(user_id, "Вы успешно распустили вашу команду.")
    await bot.answer_callback_query(callback_query.id)


if __name__ == '__main__':
    from aiogram import executor
    setup_handlers(dp, bot) 
    executor.start_webhook(
        dispatcher=dp,
        webhook_path='',
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='0.0.0.0',
        port=int(os.environ.get("PORT", 5000))
    )
