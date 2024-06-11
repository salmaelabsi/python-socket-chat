from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random  #generating random room codes
from string import ascii_uppercase

import socketio  #generating random room codes using uppercase letters

app = Flask(__name__)  #initialize app
app.config["SECRET_KEY"] = "OmarAndSalma24"  #configure flask app
socketio = SocketIO(app)  #set up socketIO integration

rooms = {}  #rooms dictionary; stores diff room info

#unique room code generation method
def generate_unique_code(Length):
    while True:
        code = ""
        for _ in range(Length):  #we don't care about no. of iterations
            code += random.choice(ascii_uppercase)  #generate a code of the desired length
         
        if code not in rooms:
            break
    return code
    
#home page
@app.route("/", methods=["POST", "GET"])  #home page route
def home():
    session.clear()  #user can't navigate after going to the home page; prevents user from typing /home or /room
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)  #set default value to false; join has an empty value
        create = request.form.get("create", False)  #set default value to false; create has an empty value

        if not name:  #if a user is attemptng to enter without specifying a username
             return render_template("home.html", error="Please enter a username!!", code=code, name=name)  #pass code & name data back to user to avoid them retyping these 

        if join != False and not code:  #if a user is attemptng to enter a room without a room code
            return render_template("home.html", error="Please enter a room code!!", code=code, name=name)
        
        room = code  #room creation
        if create != False:
            room = generate_unique_code(4)  #unique room code generation
            rooms[room] = {"members": 0, "messages": []}  #members dictionary, current room members= 0, messages list of all messages currently in chat
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist!!", code=code, name=name)
        
        session["room"] = room  #store room code
        session["name"] = name  #store user name
        return redirect(url_for("room"))

    return render_template("home.html")

#room page
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms: 
    #can't go to /room except by registering first; i.e going to /home, entering your name then either generating a code or entering a room code
        return redirect(url_for("home"));  #redirect user to home
    
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

#server receives message and retransmits it to all the connected users
@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

#flask: socket connecting
@socketio.on("connect")  #connect the rooms we've written with socketIO
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:  #make sure user has room or name
        return
    if room not in rooms:  #leave the room if it doesn't exist
        leave_room(room)
        return
    
    join_room(room)  #put the user inside a room
    send({"name": name, "message": "has entered the chatroom!"}, to=room)  #emit socket message
    rooms[room]["members"] += 1  #only when someone connects to the socket
    print(f"{name} joined room {room}")  #terminal message
    
#flask: socket connecting
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    if room in rooms:  #if the room is in our rooms
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <=0:  #if room has no members, delete room
            del rooms[room]
        
    send({"name": name, "message": "has left the chatroom."}, to=room)
    print(f"{name} left the room {room}")
    
if __name__ == "__main__":
    socketio.run(app, debug=True)  #any change we make will automatically refresh
    
#session: temporary data that is stored on a server
