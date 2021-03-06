# motors shop

## OVERVIEW:
 This project is used to give information about Pumps and Motors. This project built based on python frame work and with sqlite database.

## REQUIREMENTS:
- Python2
- Virtualenv
- sqlite
- Bootstrap4
- Html
- CSS
- Facebook authentication

## How to Run?
1. For running a serve we have to need python 2.7 or higher version

2. Install the requires modules either in virtualenv or locally
```
    pip install -r requirements.txt
```

2. To run this project execute mainFile.py

```python mainFile.py```

3. After running command the flask development server starts listening to the port 8000[https://localhost:8000](https://localhost:8000)

4. As the server is running with custom ssl certificate the browser fails to recognise the certificate as     valid cerficate

5. After loading click on advance and click proceed to unsafe.
    ![](GIF.gif)
    
6. For facebook authentication test user details are provided in reviewer notes.

# About Files:
- fb_client_secrets.json file contains facebook credentials info.
- mainDb.py is the database setup file which create tables in the sqllite database using sqlalchemy
- mainDb.db is the sqllite database file
- templates folder contains the html files which is used to render data
- requirements.txt contains all the require modules
- mainFile.py is the main file which contains all routes and logic

# Api End Points json urls:
- [https://localhost:5000/data/json](https://localhost:5000//data/json)

- This will return all the companies details with its models

- [https://local:5000/motor/jsondata](https://local:5000/motor/motorid/jsondata)

- This will return json data of company models

- [https://local:5000/motor/modal/jsondata](https://local:5000/motor/motorid/modal/modalid/jsondata)

- This will return json data model data
