from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import subprocess
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return sqlite3.connect('/root/vpn_users.db', check_same_thread=False)

@app.get("/api/user/{user_id}")
def get_user_info(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, sub_end FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user and user[1]:
        try:
            sub_end_date = datetime.datetime.strptime(user[1], "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            days_left = (sub_end_date - now).days
            
            if days_left >= 0:
                return {"status": "success", "username": user[0] or "Mijoz", "sub_end": f"{days_left} kun qoldi", "has_vpn": True}
            else:
                return {"status": "expired", "username": user[0] or "Mijoz", "sub_end": "Muddati tugagan", "has_vpn": False}
        except:
            pass
            
    return {"status": "new", "username": "Yangi foydalanuvchi", "sub_end": "Obuna yo'q", "has_vpn": False}

@app.post("/api/connect/{user_id}")
def create_vpn(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sub_end FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user or not user[0]:
        return {"status": "error", "message": "Sizda faol obuna yo'q. Iltimos, to'lov qiling."}

    try:
        result = subprocess.run(['bash', '/root/create_client.sh', f"user_{user_id}"], capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "config": result.stdout.strip()}
        else:
            return {"status": "error", "message": "Serverda xatolik yuz berdi."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
