from requests import post

data = {
  "numberId": 2725,
  "question": "Почему я плачу так много?"
}

r = post("http://localhost:8090/sdfsdfsdfsdf/qa/", json = data)
print(r.text)