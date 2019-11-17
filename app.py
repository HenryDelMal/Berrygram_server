from quart import Quart, request
from quart_cors import cors
from telethon import TelegramClient
from telethon_config import api_id, api_hash
import hypercorn.asyncio
from hypercorn.config import Config
import json


app = Quart(__name__)
app = cors(app, allow_origin="*")

client = TelegramClient('weagram', api_id, api_hash)
client.parse_mode = 'html'  # <- Render things nicely

hypercorn_config = Config()
hypercorn_config.bind = ["0.0.0.0:5000"]

async def main():
    await hypercorn.asyncio.serve(app, hypercorn_config)

## Connect the client before we start serving with Quart
@app.before_serving
async def startup():
    await client.connect()


# After we're done serving (near shutdown), clean up the client
@app.after_serving
async def cleanup():
    await client.disconnect()

@app.route('/test', methods=['GET', 'POST'])
async def test():
    return "<h1>It Works!</h1>"

@app.route('/login', methods=['GET', 'POST'])
async def login():
    form = await request.get_json()
    if 'phone' in form:
        phone_number = "+"+form['phone']
        await client.send_code_request(phone_number)
        return 'SMS/MSG Sent'
    if 'code' in form:
        await client.sign_in(code=form['code'])
        return 'Code Received'
    return 'None received'

@app.route('/send_txt', methods=['GET', 'POST'])
async def send_txt():
    form = await request.get_json()
    await client.send_message(int(form['to_user']),form['text'])
    return "Message sent"

@app.route('/check_auth', methods=['GET'])
async def check_auth():
    if await client.is_user_authorized():
        return "authenticated"
    else:
        return "nope"

@app.route('/get_my_id', methods=['GET'])
async def get_my_id():
    me = await client.get_me()
    return str(me.id)

@app.route('/get_chats', methods=['GET'])
async def get_chats():
    chat_list = []
    async for dialog in client.iter_dialogs():
        chat_list.append({'id': dialog.id, 'name': dialog.name, 'message': dialog.message.message})
    return json.dumps(chat_list)
    
@app.route('/get_msgs', methods=['GET', 'POST'])
async def get_msgs():
    message_list = []
    form = await request.get_json()
    async for message in client.iter_messages(int(form['chat_id']), reverse=False, limit=int(form['limit'])):
        message_list.append({'id': message.id, 'from': message.from_id, 'message': message.message})
    message_list.reverse()
    return json.dumps(message_list)

if __name__ == '__main__':
    client.loop.run_until_complete(main())
