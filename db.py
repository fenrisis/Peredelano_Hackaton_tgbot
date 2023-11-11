import mysql.connector
import logging

# Функция для установления соединения с базой данных
def get_connection():
    config = {
        'user': 'your username',
        'password': 'your password',
        'host': 'your host',
        'port': '????',
        'database': 'database name'
    }
    return mysql.connector.connect(**config)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def insert_user_profile(user_id, role, experience, tech_stack, idea, linkedin_profile, telegram_username, hackathon_username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Users (userId, role, experience, tech_stack, idea, linkedin_profile, telegram_username, hackathon_username) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (user_id, role, experience, tech_stack, idea, linkedin_profile, telegram_username, hackathon_username))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT role, experience, tech_stack, idea, linkedin_profile, telegram_username, hackathon_username 
    FROM Users WHERE userId = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        columns = ["role", "experience", "tech_stack", "idea", "linkedin_profile", "telegram_username", "hackathon_username"]
        return dict(zip(columns, result))
    return None

FIELD_MAP = {
    "role": "role",
    "experience": "experience",
    "tech_stack": "tech_stack",
    "idea": "idea",
    "linkedin_profile": "linkedin_profile",
    "hackathon_username": "hackathon_username"
}

def update_user_profile(user_id, field, value):
    # Проверяем, что  поле действительно существует в нашей карте
    if field not in FIELD_MAP:
        raise ValueError("Недопустимое поле для обновления")

    conn = get_connection()
    cursor = conn.cursor()
    # безопасный параметризированный запрос
    sql = f'UPDATE Users SET {FIELD_MAP[field]} = %s WHERE userId = %s'
    cursor.execute(sql, (value, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def check_user_exists(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 1 FROM Users WHERE userId = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None
    




def create_team(user_id, name, idea, required_roles):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Teams (userId, name, idea, required_roles)
    VALUES (%s, %s, %s, %s)
    ''', (user_id, name, idea, required_roles))
    conn.commit()
    team_id = cursor.lastrowid

    # Сразу делаем создателя лидером команды
    add_participant(user_id, team_id, "Лидер")

    cursor.close()
    conn.close()
    return team_id



def get_team_by_user_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT teamId, userId, name, idea, required_roles 
    FROM Teams WHERE userId = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        columns = ["teamId", "userId", "name", "idea", "required_roles"]
        return dict(zip(columns, result))
    return None



TEAM_FIELD_MAP = {
    "name": "name",
    "idea": "idea",
    "required_roles": "required_roles"
}

def update_team(team_id, field, value):
    # Проверка, что поле действительно существует
    field_key = field.lower()  # Приведение к нижнему регистру для соответствия ключам словаря
    if field_key not in TEAM_FIELD_MAP:
        raise ValueError("Недопустимое поле для обновления")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Используем безопасный параметризированный запрос
        sql = f'UPDATE Teams SET {TEAM_FIELD_MAP[field_key]} = %s WHERE teamId = %s'
        cursor.execute(sql, (value, team_id))
        conn.commit()
    except Exception as e:
        # Логирование ошибок
        logger.error(f"Error updating team: {e}")
    finally:
        cursor.close()
        conn.close()

def check_team_exists(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 1 FROM Teams WHERE userId = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def get_all_teams_with_leaders():
    conn = get_connection()
    cursor = conn.cursor()
    # Запрос объединяет таблицы Teams и Users и выбирает лидеров команд
    cursor.execute("""
    SELECT t.teamId, t.name, t.idea, t.required_roles, u.telegram_username 
    FROM Teams t
    JOIN Users u ON t.userId = u.userId
    """)
    teams = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return teams

def get_team_info_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Сначала получаем teamId для пользователя
    cursor.execute("SELECT teamId FROM Participants WHERE userId = %s", (user_id,))
    team_id_result = cursor.fetchone()
    
    # Если пользователь состоит в команде, запрашиваем информацию о команде
    if team_id_result:
        team_id = team_id_result[0]
        cursor.execute('''
        SELECT t.teamId, t.name, t.idea, t.required_roles, u.userId AS leaderId, u.telegram_username AS leaderUsername 
        FROM Teams t
        JOIN Users u ON t.userId = u.userId
        WHERE t.teamId = %s
        ''', (team_id,))
        team_info_result = cursor.fetchone()
        cursor.close()
        conn.close()

        if team_info_result:
            columns = ["teamId", "name", "idea", "required_roles", "leaderId", "leaderUsername"]
            return dict(zip(columns, team_info_result))
    
    # Если пользователь не состоит ни в одной команде
    cursor.close()
    conn.close()
    return None

def add_participant(user_id, team_id, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO Participants (userId, teamId, role) 
    VALUES (%s, %s, %s)
    ''', (user_id, team_id, role))
    conn.commit()
    cursor.close()
    conn.close()

def get_team_of_participant(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT teamId 
    FROM Participants WHERE userId = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def remove_participant(user_id, team_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    DELETE FROM Participants WHERE userId = %s AND teamId = %s
    ''', (user_id, team_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT userId, telegram_username, hackathon_username, role, experience, tech_stack, idea, linkedin_profile FROM Users")
    users = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return users

def get_team_leader_by_team_id(team_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT userId 
    FROM Teams WHERE teamId = %s
    ''', (team_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def get_user_telegram_username(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT telegram_username
    FROM Users WHERE userId = %s
    ''', (user_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None



def get_team_members_by_team_id(team_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.userId, p.role, u.telegram_username, u.hackathon_username 
    FROM Participants p 
    JOIN Users u ON p.userId = u.userId 
    WHERE p.teamId = %s
    ''', (team_id,))
    members = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return members

def get_team_of_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT teamId FROM Participants WHERE userId = %s", (user_id,))
    team = cursor.fetchone()
    cursor.close()
    conn.close()
    return team[0] if team else None

def get_user_participation(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Participants WHERE userId = %s", (user_id,))
    participation = cursor.fetchone()
    cursor.close()
    conn.close()
    return participation

def delete_team_and_participants(user_id, team_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Сначала удаляем участников команды
    cursor.execute('DELETE FROM Participants WHERE teamId = %s', (team_id,))
    # Затем удаляем саму команду
    cursor.execute('DELETE FROM Teams WHERE userId = %s', (user_id,))

    conn.commit()
    cursor.close()
    conn.close()