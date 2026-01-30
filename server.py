import threading
import socket
import time
import os

host = '0.0.0.0'
port = int(os.environ.get("PORT", 4000))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
usernames = []
last_activity = {}  
private_chats = {}  

def broadcast(message, sender=None):
    for client in clients:
        if client != sender:
            client.send(message)

def send_to_user(username, message, sender_username=None):
    """Send message to a specific user"""
    if username in usernames:
        index = usernames.index(username)
        client = clients[index]
        try:
            client.send(message)
            return True
        except:
            return False
    return False

def update_activity(client):
    """Update last activity time for a client"""
    if client in clients:
        index = clients.index(client)
        username = usernames[index]
        last_activity[username] = time.time()

def check_idle_timeout():
    """Check for idle users in private DMs and disconnect them"""
    while True:
        time.sleep(10)  
        current_time = time.time()
        
        for username in list(last_activity.keys()):
            
            if username in private_chats.values() or username in private_chats:
                if current_time - last_activity[username] > 60:  
                    
                    if username in usernames:
                        index = usernames.index(username)
                        client = clients[index]
                        
                        partner = None
                        for key, value in private_chats.items():
                            if key == username:
                                partner = value
                                break
                            elif value == username:
                                partner = key
                                break
                        
                        if partner and partner in usernames:
                            partner_index = usernames.index(partner)
                            partner_client = clients[partner_index]
                            partner_client.send(f"INFO {username} disconnected due to inactivity\n".encode('ascii'))
                            
                            if username in private_chats:
                                del private_chats[username]
                            elif partner in private_chats and private_chats[partner] == username:
                                del private_chats[partner]
                        
                        client.send("INFO You were disconnected due to inactivity\n".encode('ascii'))
                        client.close()
                        
                        if client in clients:
                            clients.remove(client)
                        if username in usernames:
                            usernames.remove(username)
                        if username in last_activity:
                            del last_activity[username]
                        
                        print(f"{username} disconnected due to inactivity in private chat")

def handle(client):
    while True:
        try:
            data = client.recv(1024)
            if not data:
                raise Exception()

            message = data.decode('ascii').strip()
            update_activity(client)  
            
            index = clients.index(client)
            username = usernames[index]

            if message == "WHO":
                for user in usernames:
                    client.send(f"USER {user}\n".encode('ascii'))

            
            elif message.startswith("MSG "):
                text = message[4:].strip()
                broadcast(
                    f"MSG {username} {text}\n".encode('ascii'),
                    sender=client
                )

            elif message.startswith("DM "):
                parts = message[3:].strip().split(' ', 1)
                if len(parts) < 2:
                    client.send("ERR Invalid DM format. Use: DM <username> <text>\n".encode('ascii'))
                    continue
                
                target_user = parts[0]
                dm_text = parts[1]
                
                if target_user == username:
                    client.send("ERR Cannot send DM to yourself\n".encode('ascii'))
                    continue
                
                if target_user not in usernames:
                    client.send(f"ERR User '{target_user}' not found\n".encode('ascii'))
                    continue
                
                private_chats[username] = target_user
                
                if send_to_user(target_user, f"DM {username} {dm_text}\n".encode('ascii')):
                    
                    client.send(f"INFO DM sent to {target_user}\n".encode('ascii'))
                else:
                    client.send(f"ERR Failed to send DM to {target_user}\n".encode('ascii'))

           
            elif message == "ENDDM":
                if username in private_chats:
                    partner = private_chats[username]
                    
                    client.send("INFO Private chat ended\n".encode('ascii'))
                    if partner in usernames:
                        send_to_user(partner, "INFO Private chat ended by other user\n".encode('ascii'))
                    del private_chats[username]
                elif username in private_chats.values():
                    
                    for initiator, receiver in list(private_chats.items()):
                        if receiver == username:
                            client.send("INFO Private chat ended\n".encode('ascii'))
                            if initiator in usernames:
                                send_to_user(initiator, "INFO Private chat ended by other user\n".encode('ascii'))
                            del private_chats[initiator]
                            break
                else:
                    client.send("INFO You are not in a private chat\n".encode('ascii'))

            
            elif not message.startswith(("WHO", "MSG ", "DM ", "ENDDM", "LOGIN ")):
                
                broadcast(
                    f"MSG {username} {message}\n".encode('ascii'),
                    sender=client
                )

        except:
            if client in clients:
                index = clients.index(client)
                username = usernames[index]
                
                
                if username in private_chats:
                    partner = private_chats[username]
                    if partner in usernames:
                        send_to_user(partner, f"INFO {username} disconnected\n".encode('ascii'))
                    del private_chats[username]
                elif username in private_chats.values():
                    for initiator, receiver in list(private_chats.items()):
                        if receiver == username:
                            if initiator in usernames:
                                send_to_user(initiator, f"INFO {username} disconnected\n".encode('ascii'))
                            del private_chats[initiator]
                            break

                clients.remove(client)
                usernames.remove(username)
                if username in last_activity:
                    del last_activity[username]
                client.close()

                broadcast(
                    f"INFO {username} disconnected\n".encode('ascii')
                )
            break

def receive():
    
    timeout_thread = threading.Thread(target=check_idle_timeout, daemon=True)
    timeout_thread.start()
    
    while True:
        client, address = server.accept()
        print(f"Connected with {str(address)}")

        try:
            data = client.recv(1024).decode('ascii').strip()

            if not data.startswith("LOGIN "):
                client.close()
                continue

            username = data[6:].strip()

            if username in usernames:
                client.send("ERR username-taken\n".encode('ascii'))
                client.close()
                continue

            usernames.append(username)
            clients.append(client)
            last_activity[username] = time.time()  

            client.send("OK\n".encode('ascii'))
            print(f"Username of client is {username}")

            thread = threading.Thread(target=handle, args=(client,))
            thread.start()

        except:
            client.close()

print("Server is running on port 4000...")
receive()