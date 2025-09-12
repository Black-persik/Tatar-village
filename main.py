import psycopg2
from typing import List, Optional, Tuple, Dict, Any
import os
import logging
import asyncio

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("Database URL must be provided or set as DATABASE_URL environment variable")
        self._create_tables()

    def _get_connection(self):
        return psycopg2.connect(self.db_url)

    def _create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Проверяем существование таблиц и обновляем их при необходимости
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            existing_tables = [table[0] for table in cursor.fetchall()]

            # Создание таблицы пользователей (если не существует)
            if 'users' not in existing_tables:
                cursor.execute('''
                    CREATE TABLE users (
                        user_id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        echpoch_score INTEGER DEFAULT 0,
                        user_name VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            else:
                # Проверяем наличие столбца telegram_id в существующей таблице
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'telegram_id'
                """)
                if not cursor.fetchone():
                    # Добавляем отсутствующий столбец
                    cursor.execute('ALTER TABLE users ADD COLUMN telegram_id BIGINT UNIQUE')
                    cursor.execute('UPDATE users SET telegram_id = user_id WHERE telegram_id IS NULL')
                    cursor.execute('ALTER TABLE users ALTER COLUMN telegram_id SET NOT NULL')

            # Создание таблицы задач (если не существует)
            if 'tasks' not in existing_tables:
                cursor.execute('''
                    CREATE TABLE tasks (
                        task_id SERIAL PRIMARY KEY,
                        cost_of_echpoch INTEGER NOT NULL,
                        task_name VARCHAR(255) NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

            # Создание таблицы связей пользователей и задач (если не существует)
            if 'user_solved_tasks' not in existing_tables:
                cursor.execute('''
                    CREATE TABLE user_solved_tasks (
                        user_id INTEGER,
                        task_id INTEGER,
                        solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, task_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id) ON DELETE CASCADE
                    )
                ''')

            # Создание индексов (если не существуют)
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'users' AND indexname = 'idx_users_telegram_id'
            """)
            if not cursor.fetchone():
                cursor.execute('CREATE INDEX idx_users_telegram_id ON users(telegram_id)')

            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'users' AND indexname = 'idx_users_score'
            """)
            if not cursor.fetchone():
                cursor.execute('CREATE INDEX idx_users_score ON users(echpoch_score)')

            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'user_solved_tasks' AND indexname = 'idx_solved_tasks_user'
            """)
            if not cursor.fetchone():
                cursor.execute('CREATE INDEX idx_solved_tasks_user ON user_solved_tasks(user_id)')

            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'user_solved_tasks' AND indexname = 'idx_solved_tasks_task'
            """)
            if not cursor.fetchone():
                cursor.execute('CREATE INDEX idx_solved_tasks_task ON user_solved_tasks(task_id)')

            conn.commit()

    # Остальные методы класса остаются без изменений
    # User operations
    def create_user(self, telegram_id: int, user_name: str, echpoch_score: int = 0) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (telegram_id, user_name, echpoch_score) VALUES (%s, %s, %s) RETURNING user_id",
                (telegram_id, user_name, echpoch_score)
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Tuple]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, telegram_id, echpoch_score, user_name FROM users WHERE telegram_id = %s",
                (telegram_id,)
            )
            return cursor.fetchone()

    def get_user(self, user_id: int) -> Optional[Tuple]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, telegram_id, echpoch_score, user_name FROM users WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()

    def update_user_score(self, user_id: int, new_score: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET echpoch_score = %s WHERE user_id = %s",
                (new_score, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def increment_user_score(self, user_id: int, increment: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET echpoch_score = echpoch_score + %s WHERE user_id = %s",
                (increment, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Task operations
    def create_task(self, task_name: str, cost_of_echpoch: int) -> int:
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT task_id, cost_of_echpoch, task_name FROM tasks WHERE task_id = %s",
                (task_id,)
            )
            return cursor.fetchone()

    def get_all_tasks(self) -> List[Tuple]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_id, cost_of_echpoch, task_name FROM tasks ORDER BY task_id")
            return cursor.fetchall()

    def update_task_cost(self, task_id: int, new_cost: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET cost_of_echpoch = %s WHERE task_id = %s",
                (new_cost, task_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Solved tasks operations
    def mark_task_as_solved(self, user_id: int, task_id: int) -> bool:
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM user_solved_tasks WHERE user_id = %s AND task_id = %s",
                (user_id, task_id)
            )
            return cursor.fetchone() is not None

    def get_user_stats(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_telegram_id(telegram_id)
        if not user:
            return None

        user_id = user[0]
        return self._get_user_stats(user_id)

    def _get_user_stats(self, user_id: int) -> Dict[str, Any]:
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

            return {
                'total_solved': total_solved,
                'total_score': total_score
            }

    # Асинхронные методы для использования в боте
    async def create_user_async(self, telegram_id: int, user_name: str, echpoch_score: int = 0) -> int:
        return await asyncio.to_thread(self.create_user, telegram_id, user_name, echpoch_score)

    async def get_user_by_telegram_id_async(self, telegram_id: int) -> Optional[Tuple]:
        return await asyncio.to_thread(self.get_user_by_telegram_id, telegram_id)

    async def get_user_stats_async(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self.get_user_stats, telegram_id)


if __name__ == "__main__":
    db = DatabaseManager("postgresql://ivanvasil4:Vasanna_7@pg4.sweb.ru:5433/ivanvasil4")
