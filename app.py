from quart import Quart, request
from quart_cors import cors
from telethon import TelegramClient
from telethon_config import api_id, api_hash
import hypercorn.asyncio
from hypercorn.config import Config
import json
import secrets
import asyncio


app = Quart(__name__)
app = cors(app, allow_origin="*")


#client = TelegramClient(None, api_id, api_hash)
#client.parse_mode = 'html'  # <- Render things nicely

hypercorn_config = Config()
hypercorn_config.bind = ["0.0.0.0:5000"]

async def main():
    await hypercorn.asyncio.serve(app, hypercorn_config)

## Connect the client before we start serving with Quart
#@app.before_serving


# After we're done serving (near shutdown), clean up the client
#@app.after_serving

@app.route('/test', methods=['GET', 'POST'])
async def test():
    return "<h1>It Works!</h1>"

@app.route('/login', methods=['GET', 'POST'])
async def login():
    form = await request.get_json()
    if 'phone' in form:
        auth_hash = secrets.token_urlsafe(16)
        print("New hash asked: "+auth_hash)
        phone_number = "+"+form['phone']
        print("Phone Number: "+phone_number)
        client_new = TelegramClient(auth_hash, api_id, api_hash)
        await client_new.connect()
        sent_code = await client_new.send_code_request(phone_number)
        print ("Phone Code Hash: "+sent_code.phone_code_hash)
        await client_new.disconnect()
        return json.dumps({0: auth_hash, 1: sent_code.phone_code_hash})
    if 'code' in form:
        print ("Hash received from client: "+ form['auth_hash'])
        print ("phone_code_hash received from client: "+ form['phone_code_hash'])
        client_new = TelegramClient(form['auth_hash'], api_id, api_hash)
        await client_new.connect()
        await client_new.sign_in(phone=form['phone_temp'], phone_code_hash=form['phone_code_hash'],code=form['code'])
        await client_new.disconnect()
        return form['auth_hash']
    

@app.route('/send_txt', methods=['GET', 'POST'])
async def send_txt():
    form = await request.get_json()
    client_new = TelegramClient(form['auth_hash'], api_id, api_hash)
    await client_new.connect()
    await client_new.send_message(int(form['to_user']),form['text'])
    await client_new.disconnect()
    return "Message sent"

@app.route('/check_auth', methods=['GET', 'POST'])
async def check_auth():
    form = await request.get_json()
    print("CHECK AUTH:")
    print(form['auth_hash'])
    client_new = TelegramClient(form['auth_hash'], api_id, api_hash)
    await client_new.connect()
    is_authorized = await client_new.is_user_authorized()
    print(is_authorized)
    if (is_authorized):
        print("THIS GUY IS AUTHORIZED!")
        await client_new.disconnect()
        return json.dumps({'authenticated': 'true'})
    else:
        return json.dumps({'authenticated': 'false'})
        await client_new.disconnect()
        print("NOT AUTHORIZED")
@app.route('/get_my_id', methods=['GET', 'POST'])
async def get_my_id():
    form = await request.get_json()
    client_new = TelegramClient(form['auth_hash'], api_id, api_hash)
    await client_new.connect()
    me = await client_new.get_me()
    await client_new.disconnect()
    return json.dumps({'id': str(me.id)})
    # return str(me.id)

@app.route('/get_chats', methods=['GET', 'POST'])
async def get_chats():
    form = await request.get_json()
    chat_list = []
    print("GET CHAT LIST:")
    print(form['auth_hash'])
    client_chats = TelegramClient(form['auth_hash'], api_id, api_hash)
    await client_chats.connect()
    async for dialog in client_chats.iter_dialogs():
        chat_list.append({'id': dialog.id, 'name': dialog.name, 'message': dialog.message.message})
    await client_chats.disconnect()
    return json.dumps(chat_list)
    
@app.route('/get_msgs', methods=['GET', 'POST'])
async def get_msgs():
    form = await request.get_json()
    message_list = []
    print("GET MESSAGE LIST:")
    print(form['auth_hash'])
    client_chats = TelegramClient(form['auth_hash'], api_id, api_hash)
    await client_chats.connect()
    form = await request.get_json()
    async for message in client_chats.iter_messages(int(form['chat_id']), reverse=False, limit=int(form['limit'])):
        message_list.append({'id': message.id, 'from': message.from_id, 'message': message.message})
    message_list.reverse()
    await client_chats.disconnect()
    return json.dumps(message_list)

if __name__ == '__main__':
    #client.loop.run_until_complete(main())
    asyncio.run(main())
