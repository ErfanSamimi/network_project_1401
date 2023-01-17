# Project members
- Erfan Samimi
- Mohammand Amin Saberi
- Abolfazl Shishegar
- Majid Bafandeh


# How to run this project for first time


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


# Attention

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
