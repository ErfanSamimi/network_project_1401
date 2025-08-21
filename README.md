
# Local Network Chat System

## Description

This project was developed as part of a University Academic Project. It implements a client-server messaging system over a local network, supporting real-time chat, file sharing, user registration/authentication, group and channel management, and persistent encrypted data storage.

## Key Learning Outcomes

- WebSocket programming for real-time communication
- Client-server architecture design and implementation
- User authentication and profile management
- Group and channel creation, membership, and role-based access control
- Secure data handling and storage using encryption
- Persistent message and media storage in a database
- Django ORM for modeling users, chatrooms, messages, and relationships
- Routing and asynchronous event handling in web applications

**Summary:** This project allowed us to practice secure real-time network programming, user and group management, and persistent data modeling using Django and WebSocket technologies.


## Project members
- Erfan Samimi
- Mohammad Amin Saberi
- Abolfazl Shishegar
- Majid Bafandeh


## How to run this project for first time


1. Clone Project
```console
git clone https://github.com/ErfanSamimi/network_project_1401.git
```


2. Create and activate a python3 virtual environment (optional)
```console
python3 -m venv venv
source venv/bin/activate
```


3. Change Directory to src/Backend
```console
cd network_project_1401/src/Backend
```

4. Install requierments.txt
```console
pip install -r requirements.txt
```

5. Create Database file
```console
python3 manage.py migrate
```

6. Collect static files
```console
python3 manage.py collectstatic
```

7. Create a 'temp' directory
```console
mkdir temp
```

8. Run server
```console
python3 manage.py runserver
```


## Attention

To create a chatroom the user's emial must be verified.

If you do not have access to an SMTP service to send verification emails, you can change user's email status to verified by doing following steps: 

1. Change working directory to backend root
```console
cd network_project_1401/src/Backend
```

2. Run a python3 shell
```console
python3 manage.py shell
```

3. Execute these commands in the shell
```python
from core.models import User
u = User.objects.get(phone_number='PHONE_NUMBER')
u.is_email_verified = True
u.save()
```
