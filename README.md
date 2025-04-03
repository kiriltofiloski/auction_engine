This is a simple auction engine app developed in Django. Thre are multiple API endpoints where registered users can create new auctions, bid on them and list through auctions and bids.

### SETUP
1. Make sure you have Docker and Docker Compose installed
2. Create `.env` file and configure these environment variables:

```
SECRET_KEY='yourSecretKey'
BRAVO_API_KEY="yourBravoMailApiKey"
```

NOTE: If you wish to test mailing iwth any other mailing service, settings must be changed for that mailer.

3. Build and start the containers

```
docker compose build
docker compose up
```

4. Open a new terminal and enter your Django app's terminal

```
docker exec -it django_app /bin/bash
```

5. From this terminal create and run migrations

```
python manage.py makemigrations
python manage.py migrate
```



### ENDPOINTS AND RESPONSES

The `test.rest` file contains examples for how to run each endpoint. You can test directly from this file as well using the REST Client VsCode extension.



### TESTS

A few tests are set up in tests.py and can be run with the following command:

```
python manage.py test
```
