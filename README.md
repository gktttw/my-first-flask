# my-first-flask
flask oauth logins

you can login by Facebook, Line, or just normal stored in db login.
Once you login with Facebook or Line, go to member page and you'll see your own name and picture accessed from 3rd party authorizaion center. 

install virtualenv

cd into the directory

`virtualenv env`

`pip3 install -r requirements.txt`

`source env/bin/activate`

I modified the flask-login package

flask-login > utils.py > logout_user()
add 
```
    if 'username' in session:
        session.pop('username')

    if 'picture_url' in session:
        session.pop('picture_url')
```

`python3 quick_start.py`
