# Playground for testing realtime data functionality


Steps:
- `docker-compose up`
- connect to the database with preffered client
- start python server `python run_instrumented.py`
- start client(s) `python test_websocket_client.py` 
- insert into database


TODO:
[] setup load script to put a "production load" on the database
[] setup a better client script
[] capture better metrics