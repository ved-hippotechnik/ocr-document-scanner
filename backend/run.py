from app import create_app

app, socketio = create_app()

if __name__ == '__main__':
    if socketio:
        socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
    else:
        app.run(debug=True, host='0.0.0.0', port=5001)
