import asyncio,os,aiohttp,urllib.parse,json
from twilio.twiml.voice_response import Gather, VoiceResponse
from asyncio import tasks
from fastapi import FastAPI,Request,Form,Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from twilio.rest import Client


# Env vars 
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
call_to = os.environ['CALL_TO']
call_from = os.environ['CALL_FROM']
base_url = os.environ['BASE_URL']

# create twilio client
client = Client(account_sid,auth_token)

# FastAPI
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Global state ↜(╰ •ω•)╯ψ Globals are evil! 
# https://softwareengineering.stackexchange.com/questions/148108/why-is-global-state-so-evil/148109#148109
tasks = {}
call_in_progress = False
failed_tasks = {}


async def caller():
    global call_in_progress
    global failed_tasks
    while True:
        for task in failed_tasks.keys():
            if not failed_tasks[task] == "ack" and not call_in_progress:
                call_in_progress = True

                client.calls.create(
                    status_callback= base_url + '/call/status',
                    status_callback_method = 'POST',
                    url = base_url + '/call/voice',
                    to = call_to,
                    from_ = call_from,
                )

        await asyncio.sleep(5)

# Go through task and add to failed tasks
async def task_scanner(failed_tasks):
    while True:
        await asyncio.sleep(5)
        for task in tasks.keys():
            if (tasks[task][1] == -1 or tasks[task][1] >= 400) and not task in failed_tasks:
                failed_tasks[task] = "failed"
                continue

            if task in failed_tasks: 
                del failed_tasks[task]

        

asyncio.create_task(task_scanner(failed_tasks))
asyncio.create_task(caller())

# Schedule url for monitoring
async def get_urls(seconds :int, url):
    while True:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    result = resp.status
                    tasks[url][1] = result
                    print(url + " " +str(result))
            except Exception as e: 
                print(e)
                tasks[url][1] = -1
        await asyncio.sleep(seconds)


# Index page shows running monitoing tasks
@app.get("/",response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "tasks":tasks})

@app.post("/",response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "tasks":tasks})

# Schedule a URL for monitoring form
@app.get("/schedule",response_class=HTMLResponse)
async def schedule_get(request: Request):
    return templates.TemplateResponse("schedule.html", {"request": request})

# Actually schedule a URL for monioring
@app.post("/schedule",response_class=HTMLResponse )
async def schedule_post(request: Request,url: str=Form(...)):
    errors = []

    try:
        task = asyncio.create_task(get_urls(10,url))
        
        if url in tasks.keys():
            print(url+" Already is monitored")
            errors.append(url+ " Is already being monitored")
            return templates.TemplateResponse("schedule-error.html", {"request": request,"errors":errors})
        
        tasks[url] = [task,0]
        response = RedirectResponse(url='/',status_code=302)
        
        return response
    except Exception as e:
        task.cancel()
        print(e)
        return templates.TemplateResponse("schedule-error.html", {"request": request,"url": url})

# twilio will post to this URL with the call status
@app.post("/call/status")
async def call_status():
    global call_in_progress
    call_in_progress = False

@app.post("/call/voice")
async def call_voice():
    print("Voice")
    resp = VoiceResponse()
    gather = Gather(num_digits=1, action='/call/gather')
    gather.say('Attention, one or more of your services are failing, please check your dashboard. Press 5 to acknowledge')
    resp.append(gather)
    return Response(content=str(resp), media_type="application/xml")


@app.post("/call/gather")
async def call_gather(request: Request):
    global failed_tasks

    resp = VoiceResponse()
    bd = await request.body()
    json_res = json.loads(json.dumps(urllib.parse.parse_qs(bd.decode('utf-8'))))
    
    if not json_res['Digits'] == ['5']:
        resp.say('You will be called untill the fault is resolved or acknowledged!')

    if json_res['Digits'] == ['5']:
        for task in failed_tasks.keys():
            failed_tasks[task] = "ack"
        resp.say('Fault acknowledged!')

    return Response(content=str(resp), media_type="application/xml")
