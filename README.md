![klapchat](klapchat.png)
# klapchat
a simple chat app made for the experience

# installing & running server
```sh
$ git clone github.com/rtweaf/klapchat
$ cd klapchat/src
$ pip install -r requirements.txt
$ uvicorn main:app --reload
```

# todo
* [ ] `changeUsername`, `changeRoomname`
* [ ] Sending images
* [ ] Audio rooms
* [x] Session expiration time and logout button

# creating new account
SQLite request
```sql
INSERT INTO users VALUES (TEXT, TEXT, TEXT)
--                       ^name ^psswd ^id
--                              hash  uuid4
```

##### thx for help [@sbdswr](https://github.com/sbdswr/)
