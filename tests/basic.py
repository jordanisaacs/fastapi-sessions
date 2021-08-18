
from . import setup

def test_get_session_without_created(setup):
  '''Create Session with GET Request'''
  client    = setup
  response  = client.get(f'/session')
  assert response.status_code == 403
  assert response.json()      == { 'detail': 'No session provided' } 
  print(response.json())

def test_create_session(setup):
  '''Create Session with POST Request, then GET session'''
  client    = setup
  name: str = 'test'

  ### Create ###
  response  = client.post(f'/session/{name}')
  assert response.status_code == 200
  assert response.text        == 'OK'
  print(response.text)

  ### Get ###
  response = client.get('/session', cookies=response.cookies)
  assert response.status_code == 200
  assert response.json()      == { 'username': name }
  print(response.json())

def test_create_session_then_clear(setup):
  '''Create Session with POST Request, then GET session'''
  client    = setup
  name: str = 'test'

  ### Create ###
  response  = client.post(f'/session/{name}')
  assert response.status_code == 200
  assert response.text        == 'OK'
  print(response.text)

  ### Clear ###
  response = client.delete('/session', cookies=response.cookies)
  assert response.status_code == 200
  assert response.text        == 'deleted session' 

  ### Get ###
  response = client.get('/session', cookies=response.cookies)
  assert response.status_code == 403
  assert response.json()      == { 'detail': 'No session provided' } 
  print(response.json())