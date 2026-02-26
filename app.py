import os
import time
import threading
import requests
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bot_secret_key'
# eventlet use kar rahe hain taaki Render par smoothly chale
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Bot ka global status store karne ke liye
bot_status = {
    "is_running": False,
    "url": "",
    "interval_seconds": 0,
    "open_count": 0,
    "time_left": 0,
    "current_action": "Stopped"
}

def bot_task():
    global bot_status
    while bot_status["is_running"]:
        
        # 1. Link open karna
        bot_status["current_action"] = "Opening Link..."
        bot_status["time_left"] = 0
        socketio.emit('update_status', bot_status)
        
        try:
            # Fake user-agent taaki website block na kare
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            requests.get(bot_status["url"], headers=headers, timeout=15)
            bot_status["open_count"] += 1
        except Exception as e:
            print(f"Error opening link: {e}")
            pass # Error aaye tab bhi bot rukna nahi chahiye
        
        # 2. Link open hone ke baad 5 second wait karna (Jaisa aapne kaha)
        bot_status["current_action"] = "Waiting 5 seconds..."
        for sec in range(5, 0, -1):
            if not bot_status["is_running"]:
                break
            bot_status["time_left"] = sec
            socketio.emit('update_status', bot_status)
            time.sleep(1)

        if not bot_status["is_running"]:
            break

        # 3. Next link open karne ke liye user ke set kiye interval ka countdown
        bot_status["current_action"] = "Waiting for next open"
        for remaining in range(bot_status["interval_seconds"], 0, -1):
            if not bot_status["is_running"]:
                break
            bot_status["time_left"] = remaining
            socketio.emit('update_status', bot_status)
            time.sleep(1)

@app.route('/')
def index():
    # Yeh aapke templates folder se HTML file load karega
    return render_template('index.html')

@socketio.on('start_bot')
def handle_start(data):
    global bot_status
    # Agar bot pehle se nahi chal raha, tabhi start karein
    if not bot_status["is_running"]:
        bot_status["url"] = data['url']
        bot_status["interval_seconds"] = int(data['interval'])
        bot_status["open_count"] = 0
        bot_status["is_running"] = True
        
        # Background thread start karna taaki server hang na ho
        threading.Thread(target=bot_task).start()

@socketio.on('stop_bot')
def handle_stop():
    global bot_status
    bot_status["is_running"] = False
    bot_status["current_action"] = "Stopped"
    bot_status["time_left"] = 0
    socketio.emit('update_status', bot_status)

@socketio.on('get_status')
def send_status():
    global bot_status
    socketio.emit('update_status', bot_status)

if __name__ == '__main__':
    # Render khud port assign karta hai, isliye environ use kiya hai
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
