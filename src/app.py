from aiohttp import web
import asyncio
import motor.motor_asyncio
import config
from time import time



from json import JSONEncoder
from bson import ObjectId

class bb(JSONEncoder):
  def default(self, o):
    if isinstance(o, ObjectId):
      return str(o)
    return JSONEncoder.default(self, o)

dumps = bb().encode


async def createQA(request):
  key = request.match_info['key']
  if key not in config.KEYS:
    raise RuntimeError("Невалидный ключ!")
  json = await request.json()
  msg = {
    "key": key,
    "numberId": json["numberId"],
    "question": json["question"],
    "questionTime": int(time())
  }

  if "questionFiles" in json:
    msg["questionFiles"] = json["questionFiles"]

  if "answerFiles" in json:
    msg["answerFiles"] = json["answerFiles"]

  await request.db.qa.insert(msg)
  return web.json_response(msg, dumps = dumps)



async def getQAs(request):
  qas = []
  key = request.match_info['key']
  if key not in config.KEYS:
    raise RuntimeError("Невалидный ключ!")

  status = request.query.get("status", None)
  numberId = request.query.get("numberId", None)
  limit = int(request.query.get("limit", 0))

  query = {"key": key}

  # фильтрация по статусу
  if status and status == "noanswer":
    query["userId"] = {"$exists": False}
  if status and status == "answered":
    query["userId"] = {"$exists": True}

  # фильтрация по номерму лицевого счета
  if numberId:
    query["numberId"] = int(numberId)

  async for row in request.db.qa.find(query, {"key": 0}).sort([("questionTime", -1)]).limit(limit):
    qas.append(row)
  return web.json_response(qas, dumps = dumps)



async def getQA(request):
  key = request.match_info['key']
  qaId = request.match_info['qaId']
  if key not in config.KEYS:
    raise RuntimeError("Невалидный ключ!")
  qa = await request.db.qa.find_one({"key": key, "_id": ObjectId(qaId)}, {"key": 0})
  return web.json_response(qa, dumps = dumps)



async def updateQA(request):
  key = request.match_info['key']
  qaId = request.match_info['qaId']
  if key not in config.KEYS:
    raise RuntimeError("Невалидный ключ!")
  json = await request.json()
  qa = await request.db.qa.find_one({"key": key, "_id": ObjectId(qaId)}, {"key": 0})
  update = {
    "userId": json["userId"],
    "answer": json["answer"],
    "answerTime": int(time())
  }
  await request.db.qa.update_one({"_id": ObjectId(qaId)}, {"$set": update})
  qa = await request.db.qa.find_one({"key": key, "_id": ObjectId(qaId)}, {"key": 0})
  return web.json_response(qa, dumps = dumps)



async def db_handler(app, handler):
  async def middleware(request):
    request.db = app.db
    response = await handler(request)
    return response
  return middleware



app = web.Application(middlewares = [db_handler], loop = asyncio.get_event_loop())
app.client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGO_DSN)
app.db = app.client.qa


app.router.add_post('/{key}/qa/', createQA)
app.router.add_get('/{key}/qa/', getQAs)
app.router.add_get('/{key}/qa/{qaId}', getQA)
app.router.add_put('/{key}/qa/{qaId}', updateQA)
app.channels = {}


if __name__ == "__main__":
  web.run_app(app, port = config.PORT)