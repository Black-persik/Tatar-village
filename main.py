import psycopg2
from typing import List, Optional, Tuple
import os


class DatabaseManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("Database URL must be provided or set as DATABASE_URL environment variable")
        self._create_tables()

    def _get_connection(self):
        """Создание соединения с базой данных PostgreSQL"""
        return psycopg2.connect(self.db_url)

    def _create_tables(self):
        """Создание таблиц если они не существуют"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Создание таблицы пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    echpoch_score INTEGER DEFAULT 0,
                    user_name VARCHAR(255) NOT NULL UNIQUE
                )
            ''')

            # Создание таблицы задач
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id SERIAL PRIMARY KEY,
                    cost_of_echpoch INTEGER NOT NULL,
                    task_name VARCHAR(255) NOT NULL UNIQUE
                )
            ''')

            # Создание таблицы связей пользователей и задач (решенные задачи)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_solved_tasks (
                    user_id INTEGER,
                    task_id INTEGER,
                    solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, task_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                    FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE
                )
            ''')

            # Создание индексов для улучшения производительности
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_score ON users(echpoch_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_solved_tasks_user ON user_solved_tasks(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_solved_tasks_task ON user_solved_tasks(task_id)')

            conn.commit()

    # User operations
    def create_user(self, user_name: str, echpoch_score: int = 0) -> int:
        """Создание нового пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (user_name, echpoch_score) VALUES (%s, %s) RETURNING user_id",
                (user_name, echpoch_score)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id

    def get_user(self, user_id: int) -> Optional[Tuple]:
        """Получение пользователя по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, echpoch_score, user_name FROM users WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()

    def get_user_by_name(self, user_name: str) -> Optional[Tuple]:
        """Получение пользователя по имени"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, echpoch_score, user_name FROM users WHERE user_name = %s",
                (user_name,)
            )
            return cursor.fetchone()

    def update_user_score(self, user_id: int, new_score: int) -> bool:
        """Обновление счета пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET echpoch_score = %s WHERE user_id = %s",
                (new_score, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def increment_user_score(self, user_id: int, increment: int) -> bool:
        """Увеличение счета пользователя на указанное значение"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET echpoch_score = echpoch_score + %s WHERE user_id = %s",
                (increment, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя (каскадное удаление благодаря ON DELETE CASCADE)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Task operations
    def create_task(self, task_name: str, cost_of_echpoch: int) -> int:
        """Создание новой задачи"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (task_name, cost_of_echpoch) VALUES (%s, %s) RETURNING task_id",
                (task_name, cost_of_echpoch)
            )
            task_id = cursor.fetchone()[0]
            conn.commit()
            return task_id

    def get_task(self, task_id: int) -> Optional[Tuple]:
        """Получение задачи по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT task_id, cost_of_echpoch, task_name FROM tasks WHERE task_id = %s",
                (task_id,)
            )
            return cursor.fetchone()

    def get_all_tasks(self) -> List[Tuple]:
        """Получение всех задач"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_id, cost_of_echpoch, task_name FROM tasks ORDER BY task_id")
            return cursor.fetchall()

    def update_task_cost(self, task_id: int, new_cost: int) -> bool:
        """Обновление стоимости задачи"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET cost_of_echpoch = %s WHERE task_id = %s",
                (new_cost, task_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Удаление задачи (каскадное удаление благодаря ON DELETE CASCADE)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Solved tasks operations
    def mark_task_as_solved(self, user_id: int, task_id: int) -> bool:
        """Отметка задачи как решенной пользователем"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Проверяем существование пользователя и задачи
                cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                if not cursor.fetchone():
                    return False

                cursor.execute("SELECT 1 FROM tasks WHERE task_id = %s", (task_id,))
                if not cursor.fetchone():
                    return False

                # Пытаемся добавить запись о решенной задаче
                cursor.execute(
                    "INSERT INTO user_solved_tasks (user_id, task_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (user_id, task_id)
                )

                if cursor.rowcount == 0:
                    # Задача уже была решена
                    return False

                # Обновляем счет пользователя
                cursor.execute(
                    "UPDATE users SET echpoch_score = echpoch_score + " +
                    "(SELECT cost_of_echpoch FROM tasks WHERE task_id = %s) " +
                    "WHERE user_id = %s",
                    (task_id, user_id)
                )

                conn.commit()
                return True

            except psycopg2.Error as e:
                conn.rollback()
                print(f"Error marking task as solved: {e}")
                return False

    def get_solved_tasks(self, user_id: int) -> List[Tuple]:
        """Получение всех решенных задач пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT t.task_id, t.cost_of_echpoch, t.task_name, ust.solved_at
                FROM tasks t
                JOIN user_solved_tasks ust ON t.task_id = ust.task_id
                WHERE ust.user_id = %s
                ORDER BY ust.solved_at DESC
            ''', (user_id,))
            return cursor.fetchall()

    def is_task_solved(self, user_id: int, task_id: int) -> bool:
        """Проверка, решена ли задача пользователем"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM user_solved_tasks WHERE user_id = %s AND task_id = %s",
                (user_id, task_id)
            )
            return cursor.fetchone() is not None

    def get_user_leaderboard(self, limit: int = 10) -> List[Tuple]:
        """Получение таблицы лидеров"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, user_name, echpoch_score
                FROM users
                ORDER BY echpoch_score DESC
                LIMIT %s
            ''', (limit,))
            return cursor.fetchall()

    def get_user_stats(self, user_id: int) -> dict:
        """Получение статистики пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Общее количество решенных задач
            cursor.execute(
                "SELECT COUNT(*) FROM user_solved_tasks WHERE user_id = %s",
                (user_id,)
            )
            total_solved = cursor.fetchone()[0]

            # Общее количество очков
            cursor.execute(
                "SELECT echpoch_score FROM users WHERE user_id = %s",
                (user_id,)
            )
            total_score = cursor.fetchone()[0]

            # Позиция в рейтинге
            cursor.execute('''
                SELECT rank FROM (
                    SELECT user_id, RANK() OVER (ORDER BY echpoch_score DESC) as rank
                    FROM users
                ) ranked WHERE user_id = %s
            ''', (user_id,))
            rank = cursor.fetchone()[0] if cursor.rowcount > 0 else None

            return {
                'total_solved': total_solved,
                'total_score': total_score,
                'rank': rank
            }



db = DatabaseManager("postgresql://ivanvasil4:Vasanna_7@pg4.sweb.ru:5433/ivanvasil4")


# Создание пользователей
user1_id = db.create_user("Alice", 0)
user2_id = db.create_user("Bob", 0)

# Создание задач
task1_id = db.create_task("Easy Task", 10)
task2_id = db.create_task("Medium Task", 20)
task3_id = db.create_task("Hard Task", 50)

# Отметка решенных задач
db.mark_task_as_solved(user1_id, task1_id)
db.mark_task_as_solved(user1_id, task2_id)
db.mark_task_as_solved(user2_id, task1_id)

# Получение информации
user1 = db.get_user(user1_id)
print(f"User 1: {user1}")

solved_tasks = db.get_solved_tasks(user1_id)
print(f"Solved tasks by user 1: {solved_tasks}")

leaderboard = db.get_user_leaderboard()
print("Leaderboard:", leaderboard)

stats = db.get_user_stats(user1_id)
print(f"User 1 stats: {stats}")