from aiogram import types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from aiogram.types import Message
import db 
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_handlers(dp, bot):


 class ProfileForm(StatesGroup):
    role = State()
    experience = State()
    tech_stack = State()
    idea = State()
    linkedin = State()
    hackathon_username = State()


 class EditProfileForm(StatesGroup):
    select_field = State()
    new_value = State()

 class TeamForm(StatesGroup):
    name = State()
    idea = State()
    required_roles = State()

 class EditTeamForm(StatesGroup):
    select_field = State()
    new_value = State()


 def role_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    roles = ["Backend", "Frontend", "Mobile", "Full-stack", "DevOps", "QA", "UI Designer", "UX Designer", "ML", "PM"]
    for role in roles:
        markup.add(KeyboardButton(role))
    return markup
 
 def experience_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    experiences = ["До года", "1-3 года", "3-5 лет", "Свыше 5 лет", "Не работаю"]
    for experience in experiences:
        markup.add(KeyboardButton(experience))
    return markup
 
 
 @dp.message_handler(Command("profile"), state=None)
 async def profile_command(message: Message):
    user_id = message.from_user.id
    if db.check_user_exists(user_id):
        user_profile = db.get_user_profile(user_id)
        profile_text = (
            f"Роль: {user_profile['role']}\n"  
            f"Опыт: {user_profile['experience']}\n"
            f"Технологический стек: {user_profile['tech_stack']}\n"
            f"Идея: {user_profile['idea']}\n"
            f"LinkedIn: {user_profile['linkedin_profile']}\n"
            f"Hackathon Username: {user_profile.get('hackathon_username')}\n\n"
            "Внести изменения в профиль можно \n[/editprofile]."
        )
        await message.answer(profile_text)
    else:
        markup = role_keyboard()
        await message.answer("Выберите вашу роль:", reply_markup=markup)
        await ProfileForm.role.set()

 @dp.message_handler(state=ProfileForm.role)
 async def process_role(message: Message, state: FSMContext):
    roles = ["Backend", "Frontend", "Mobile", "DevOps", "Full-stack", "QA", "UI Designer", "UX Designer", "ML", "PM"]
    if message.text in roles:
        await state.update_data(role=message.text)
        markup = experience_keyboard()
        await message.answer("Выберите ваш опыт работы:", reply_markup=markup)
        await ProfileForm.experience.set()
    else:
        await message.answer('К сожалению, я не настолько умен, чтобы ответить на твое сообщение :('
                             '\nНажми на кнопку для продолжения (иногда нижнее меню сворачивается, '
                             'можно развернуть его кнопкой вроде этой: 🎛).'
                             , reply_markup=role_keyboard())

 @dp.message_handler(state=ProfileForm.experience)
 async def process_experience(message: Message, state: FSMContext):
    experiences = ["До года", "1-3 года", "3-5 лет", "Свыше 5 лет", "Не работаю"]
    if message.text in experiences:
        await state.update_data(experience=message.text)
        await message.answer("Введите ваш технологический стек:", reply_markup=ReplyKeyboardRemove())
        await ProfileForm.tech_stack.set()
    else:
        await message.answer('Выберите ваш опыт работы из предложенных вариантов:', reply_markup=experience_keyboard())
 
 
 @dp.message_handler(state=ProfileForm.tech_stack)
 async def process_tech_stack(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Стек не может начинаться со слеша (/). Пожалуйста, введите другое название.")
        return
    await state.update_data(tech_stack=message.text)
    await message.answer("Есть ли у вас идея для стартапа? Если да, опишите кратко:", reply_markup=ReplyKeyboardRemove())
    await ProfileForm.idea.set()

 @dp.message_handler(state=ProfileForm.idea)
 async def process_idea(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Идея не может начинаться со слеша (/). Пожалуйста, введите другое название.")
        return
    await state.update_data(idea=message.text)
    await message.answer("Введите ссылку на ваш профиль LinkedIn:", reply_markup=ReplyKeyboardRemove())
    await ProfileForm.linkedin.set()

 @dp.message_handler(state=ProfileForm.linkedin)
 async def process_linkedin(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Ссылка на LinkedIn не может начинаться со слеша (/). Пожалуйста, введите другое название.")
        return
    await state.update_data(linkedin_profile=message.text)
    await message.answer("Введите ваше имя пользователя для хакатона ")
    await ProfileForm.hackathon_username.set()

 @dp.message_handler(state=ProfileForm.hackathon_username)
 async def process_hackathon_username(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Имя пользователя для хакатона не может начинаться со слеша (/). Пожалуйста, введите другое название.")
        return
    # Проверка, пропустил ли пользователь ввод имени пользователя для хакатона
    hackathon_username = message.text if message.text != '-' else None
    await state.update_data(hackathon_username=hackathon_username)

    # Получаем данные пользователя из состояния
    user_data = await state.get_data()

    # Получение telegram_username, если он существует
    telegram_username = None
    if message.from_user.username:
        telegram_username = "@" + message.from_user.username

    # Вызов функции вставки в базу данных с обоими именами пользователей
    db.insert_user_profile(
        message.from_user.id, 
        user_data['role'], 
        user_data['experience'], 
        user_data['tech_stack'], 
        user_data['idea'], 
        user_data['linkedin_profile'],
        telegram_username,  # сохраняем telegram_username если он есть
        user_data.get('hackathon_username')  # сохраняем hackathon_username
    )
    await message.answer(
        "Профиль успешно сохранен!\n"
        "Посмотреть что получилось: [/profile].\n"
        "Но если хотите внести изменения, используйте [/editprofile]."
    )
    await state.finish()

 
 
 def generate_edit_menu():
    markup = InlineKeyboardMarkup()
    items = [
        ("Роль", "edit_role"),
        ("Опыт", "edit_experience"),
        ("Тех. стек", "edit_tech_stack"),
        ("Идея", "edit_idea"),
        ("LinkedIn", "edit_linkedin"),
        ("Hackathon_username", "edit_hackathon_username")
    ]
    for text, callback_data in items:
        markup.add(InlineKeyboardButton(text, callback_data=callback_data))
    markup.add(InlineKeyboardButton("Отмена", callback_data="cancel_edit")) 
    return markup

 @dp.message_handler(Command("editprofile"), state=None)
 async def edit_profile_start(message: Message):
    markup = generate_edit_menu()
    await message.answer("Выберите поле для редактирования:", reply_markup=markup)
    await EditProfileForm.select_field.set()

 @dp.callback_query_handler(state=EditProfileForm.select_field)
 async def choose_field_to_edit(callback_query: CallbackQuery, state: FSMContext):
    field_map = {
        "edit_role": "role",
        "edit_experience": "experience",
        "edit_tech_stack": "tech_stack",
        "edit_idea": "idea",
        "edit_linkedin": "linkedin_profile",
        "edit_hackathon_username": "hackathon_username" 
    }
    await bot.answer_callback_query(callback_query.id)

    selected_field = callback_query.data
    if selected_field == "cancel_edit":
        await bot.send_message(callback_query.from_user.id, "Редактирование отменено. Посмотреть что получилось: [/profile].")
        await state.finish()
        return

    if selected_field not in field_map:
        await bot.send_message(callback_query.from_user.id, "Пожалуйста, выберите корректное поле из списка.")
        return

    await state.update_data(field_to_edit=field_map[selected_field])
    await bot.send_message(callback_query.from_user.id, f"Введите новое значение для поля '{selected_field.split('_')[1]}':")
    await EditProfileForm.new_value.set()

 @dp.message_handler(state=EditProfileForm.new_value)
 async def process_new_value(message: Message, state: FSMContext):
    user_data = await state.get_data()
    field_to_edit = user_data['field_to_edit']

    db.update_user_profile(message.from_user.id, field_to_edit, message.text)
    await message.answer(f"Значение поля '{field_to_edit}' успешно обновлено! ")

    markup = generate_edit_menu()
    await message.answer("Выберите следующее поле для редактирования или завершите редактирование:", reply_markup=markup)
    await EditProfileForm.select_field.set()

 @dp.callback_query_handler(lambda c: c.data == "cancel_edit", state="*")
 async def cancel_edit(callback_query: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Редактирование отменено. Профиль: [/profile]")
    await state.finish()


 @dp.message_handler(Command("team"), state=None)
 async def team_command(message: Message):
    user_id = message.from_user.id
    user_profile = db.get_user_profile(user_id)

    if user_profile and all(user_profile.values()):  
        # Проверяем, состоит ли пользователь уже в какой-либо команде
        team_id = db.get_team_of_user(user_id)
        if team_id:
            # Если уже в команде
            await message.answer("Вы уже состоите в команде. Вы не можете создать новую команду.")
        else:
            # Пользователь не в команде, продолжаем процесс создания команды
            await message.answer("Вы еще не создали команду. Введите название вашей команды:")
            await TeamForm.name.set()
    else:
        await message.answer("Вы не можете создать команду, пока не заполните свой профиль. Пожалуйста, заполните его с помощью команды [/profile].")

 
 @dp.message_handler(state=TeamForm.name)
 async def process_team_name(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Название команды не может начинаться со слеша (/). Пожалуйста, введите другое название.")
        return
    await state.update_data(name=message.text)
    await message.answer("Введите идею вашей команды:")
    await TeamForm.idea.set()

 
 @dp.message_handler(state=TeamForm.idea)
 async def process_team_idea(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Описание идеи не может начинаться со слеша (/). Пожалуйста, введите другое описание.")
        return
    await state.update_data(idea=message.text)
    await message.answer("Выберите требуемые роли для вашей команды:", reply_markup=role_keyboard())
    await TeamForm.required_roles.set()

 
 @dp.message_handler(state=TeamForm.required_roles)
 async def process_team_roles(message: Message, state: FSMContext):
    if message.text.startswith("/"):
        await message.answer("Требуемые роли не могут начинаться со слеша (/). Пожалуйста, введите другие роли.")
        return
    await state.update_data(required_roles=message.text)
    team_data = await state.get_data()
    team_id = db.create_team(
        message.from_user.id,
        team_data['name'], 
        team_data['idea'], 
        team_data['required_roles']
    )
    await message.answer(
        "Команда успешно создана!\n"
        "Информация о команде: [/myteam].\n"
        "Редактировать информацию о команде [/editteam].",
        reply_markup=ReplyKeyboardRemove()  # Удаление клавиатуры
    )
    await state.finish()
 
 def generate_team_edit_menu():
    markup = InlineKeyboardMarkup()
    items = [
        ("Название команды", "edit_name"),
        ("Идея", "edit_idea"),
        ("Требуемые роли", "edit_required_roles")
    ]
    for text, callback_data in items:
        markup.add(InlineKeyboardButton(text, callback_data=callback_data))
    markup.add(InlineKeyboardButton("Отмена", callback_data="cancel_team_edit"))
    return markup
 
 @dp.message_handler(Command("editteam"), state=None)
 async def edit_team_command(message: Message, state: FSMContext):
    # Получаем информацию о команде, где пользователь является создателем (лидером)
    team_info = db.get_team_by_user_id(message.from_user.id)
    if team_info:
        # Пользователь является лидером, продолжаем.
        markup = generate_team_edit_menu()
        await message.answer("Выберите поле для редактирования:", reply_markup=markup)
        await EditTeamForm.select_field.set()
        await state.update_data(team_id=team_info['teamId'])
    else:
        # Пользователь не является лидером команды.
        await message.answer("Вы не являетесь лидером команды или команда не найдена.")



 @dp.callback_query_handler(state=EditTeamForm.select_field)
 async def choose_team_field_to_edit(callback_query: CallbackQuery, state: FSMContext):
    field_map = {
        "edit_name": "name",
        "edit_idea": "idea",
        "edit_required_roles": "required_roles"
    }
    await bot.answer_callback_query(callback_query.id)

    selected_field = callback_query.data
    if selected_field == "cancel_team_edit":
        await bot.send_message(callback_query.from_user.id, "Редактирование команды отменено.")
        await state.finish()
        return

    if selected_field not in field_map:
        await bot.send_message(callback_query.from_user.id, "Пожалуйста, выберите корректное поле из списка.")
        return

    await state.update_data(field_to_edit=field_map[selected_field])
    await bot.send_message(callback_query.from_user.id, f"Введите новое значение для поля '{selected_field.split('_')[1]}':")
    await EditTeamForm.new_value.set()

 @dp.message_handler(state=EditTeamForm.new_value)
 async def process_team_new_value(message: Message, state: FSMContext):
    team_data = await state.get_data()
    team_id = team_data.get('team_id')
    if team_id:
        # Теперь обновляем команду с этим ID.
        db.update_team(team_id, team_data['field_to_edit'], message.text)
        await message.answer(f"Значение поля '{team_data['field_to_edit']}' успешно обновлено!")
        await state.finish()
    else:
        # Если team_id не найден в состоянии, сообщаем об ошибке.
        await message.answer("Произошла ошибка. Невозможно обновить команду.")
 
 
