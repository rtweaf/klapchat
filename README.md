# klapchat
A simple websocket chat, based on Django framework

## Running
```sh
# install the requirements
pip install -r requirements.txt

# run database on docker
docker run -p 6379:6379 -d redis:5

# run django server
python manage.py runserver
```