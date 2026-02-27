import os
import requests
from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bot_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

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
        
        bot_status["current_action"] = "Opening Link..."
        bot_status["time_left"] = 0
        socketio.emit('update_status', bot_status)
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            requests.get(bot_status["url"], headers=headers, timeout=15)
            bot_status["open_count"] += 1
        except Exception as e:
            print(f"Error opening link: {e}")
            pass
        
        bot_status["current_action"] = "Waiting 5 seconds..."
        for sec in range(5, 0, -1):
            if not bot_status["is_running"]:
                break
            bot_status["time_left"] = sec
            socketio.emit('update_status', bot_status)
            socketio.sleep(1) # Yahan fix kiya hai taaki server hang na ho

        if not bot_status["is_running"]:
            break

        bot_status["current_action"] = "Waiting for next open"
        for remaining in range(bot_status["interval_seconds"], 0, -1):
            if not bot_status["is_running"]:
                break
            bot_status["time_left"] = remaining
            socketio.emit('update_status', bot_status)
            socketio.sleep(1) # Yahan fix kiya hai

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_bot')
def handle_start(data):
    global bot_status
    if not bot_status["is_running"]:
        bot_status["url"] = data['url']
        bot_status["interval_seconds"] = int(data['interval'])
        bot_status["open_count"] = 0
        bot_status["is_running"] = True
        
        # Thread ki jagah background task use kiya hai
        socketio.start_background_task(bot_task)

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
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
