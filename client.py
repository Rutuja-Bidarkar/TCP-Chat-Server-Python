import socket
import threading
import sys

HOST = "web-production-57ef93.up.railway.app"
PORT = 4000  

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def receive():
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if not message:
                break
            print(message.strip())
        except:
            client.close()
            print("\nDisconnected from server")
            sys.exit(1)
            break

def write():
    while True:
        try:
            msg = input().strip()
            client.send((msg + "\n").encode('ascii'))
        except (EOFError, KeyboardInterrupt):
            client.close()
            print("\nYou left the chat")
            sys.exit(0)
            break

print("Welcome to the chat!")
print("First, login with: LOGIN <username>")
print("\nCommands:")
print("  WHO - List online users")
print("  MSG <text> - Send message to general chat")
print("  DM <username> <text> - Send private message")
print("  ENDDM - End current private chat")
print("\nNote: 60-second inactivity timeout applies only in private DMs")

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()