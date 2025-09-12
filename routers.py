from main import DatabaseManager
db = DatabaseManager()

def create_user(name: str, echpochmac_score = 0):
    db.create_user(name, echpochmac_score)

def get_user(name:str, user_id: int):
    db.get_user(user_id)

def update_user_score(user_id: int, score: int):
    db.update_user_score(user_id, score)

def increment_user_score(user_id, score: int):
    db.increment_user_score(user_id, score)

def create_task(name: str, echpochmac_score = 0):
    db.create_task(name, echpochmac_score)

def get_task(task_id: int):
    db.get_task(task_id)

def mark_task_as_solved(user_id: int, task_id: int):
    db.mark_task_as_solved(user_id, task_id)

def get_stats(user_id: int):
    db.get_user_stats(user_id)