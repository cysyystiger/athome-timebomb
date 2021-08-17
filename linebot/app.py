from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *


#======這裡是呼叫的檔案內容=====
from Function import *
from picture import *
#======這裡是呼叫的檔案內容=====

#======python的函數庫==========
import tempfile, os
import datetime
import time
from collections import Counter
from queue import Queue
from random import shuffle
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi('1ZnSGdtE+Xyos3IWSbxbxxneoWx8q+ZV5l/3Xo2zERMVAdb9FVUvbZnQG+9TxhjSWpiPWeI1UTEfLPtSFy9vWtyWYwxAMDBg6FEtUkN2DgmGedR6lgwv0lmwVTFYVR/Tkjzouo3bvqULSNqUvCRv8gdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('c9acbaf332f854c886f36f383d664f61')

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

class Data():
    def __init__(self):
        self.reset()
    def reset(self):
        self.state = 'none' #none->created->setting->gaming
        self.player = set()
        self.seat = set()
        self.role = ['紅軍', '紅軍', '藍軍', '藍軍', '藍軍', '藍軍', '藍軍', '紅軍']
        self.allcard = []
        self.cutcard = []
        self.playercard = {}
        self.scissors = 0
        self.nextplayerseat = 0
        self.round = 0
        self.times = 0

data = Data()

def Verify(func):
    def wrapper(**kwargs):
        user_id = kwargs['user_id']
        data = kwargs['data']
        if user_id not in data.player:
            return TextSendMessage(text='不是玩家')
        else:
            return func(**kwargs)
    return wrapper

def VerifyChoosePlayer(func):
    @Verify
    def wrapper(**kwargs):
        user_id = kwargs['user_id']
        data = kwargs['data']
        idx = data.player.index(user_id)
        seat = data.seat[idx]
        if seat != data.scissors:
            item = []
            for s in sorted(data.seat):
                if s != data.scissors:
                    item.append(
                        QuickReplyButton(action=PostbackAction(label=str(s), data=str(s)))
                    )
            quickReply = QuickReply(
                items = item
            )
            txt='你的角色不能執行此動作'
            return TextSendMessage(text=txt, quick_reply=quickReply)
        else:
            return func(**kwargs)
    return wrapper

def VerifyChooseCard(func):
    @Verify
    def wrapper(**kwargs):
        user_id = kwargs['user_id']
        data = kwargs['data']
        idx = data.player.index(user_id)
        seat = data.seat[idx]
        if seat != data.scissors:
            txt='你的角色不能執行此動作'
            return TextSendMessage(text=txt)
        else:
            return func(**kwargs)
    return wrapper

def IsState(states=None):
    def decorator(func):
        def wrapper(**kwargs):
            data = kwargs['data']
            if data.state not in states:
                return TextSendMessage(text='現在不能做此動作')
            else:
                return func(**kwargs)
        return wrapper
    return decorator

@IsState(states = ['none'])
def CreateGame(data=None):
    data.state = 'created'
    buttons = ButtonsTemplate(
                    title = "成功建立房間",
                    text = "大家請私訊機器人：加 or +",
                    actions = [
                        PostbackTemplateAction(
                            label = '人數',
                            data = '人數'
                        ),
                        PostbackTemplateAction(
                            label = '開始',
                            data = '開始'
                        )
                    ]
                )
    return TemplateSendMessage(alt_text="成功建立房間", template=buttons)

@IsState(states = ['created'])
def PlayOne(user_id=None, data=None):
    print(user_id)
    if user_id in data.player:
        return TextSendMessage(text='已經是玩家')
    elif len(data.player) == 8:
        return TextSendMessage(text='玩家數已滿')
    else:
        data.player.add(user_id)
        seat = len(data.player)
        data.seat.add(seat)
        buttons = ButtonsTemplate(
                    title = "成功加入遊戲",
                    text = "等待群組開始遊戲後\n點擊'身分'",
                    actions = [
                        PostbackTemplateAction(
                            label = '身分',
                            data = '身分'
                        ),
                        PostbackTemplateAction(
                            label = '看牌',
                            data = '看牌'
                        ),
                    ]
                )
        return TemplateSendMessage(alt_text="成功加入遊戲", template=buttons)

@IsState(states = ['created'])
def PlayNum(data=None):
    return TextSendMessage(text='目前 '+str(len(data.player))+' 人在房間')

@IsState(states = ['created'])
def StartGame(data=None):
    if len(data.player) < 4: #<4
        return TextSendMessage(text='人數不足4人無法進行遊戲')
    else:
        data.seat = sorted(data.seat)
        shuffle(data.seat)
        data.player = sorted(data.player)
        shuffle(data.player)
        n = len(data.player)
        if n in [5, 6, 8]:#[5, 6, 8]
            data.role = data.role[:n]
        else:#把角色和牌都先發好
            import random as r
            data.role = data.role[:n+1]
            data.role.pop(r.randint(0, n))
        for i in range(4*n-1):
            data.allcard.append('安全引線')
        for i in range(n):
            data.allcard.append('解除引線')
        data.allcard.append('炸彈')
        shuffle(data.allcard)
        for user in data.player:
            idx = data.player.index(user)
            seat = data.seat[idx]
            data.playercard[seat] = data.allcard[seat*5-5:seat*5]
        buttons = ButtonsTemplate(
            title = '遊戲開始',
            text = "請私訊點擊'身分'和'看牌'",
            actions = [
                PostbackTemplateAction(
                    label = '發剪刀',
                    data = '發剪刀'
                    ),
            ]
        )
        data.round += 1
        data.state = 'setting'
    return TemplateSendMessage(alt_text="請私訊點擊'身分'和'看牌'", template=buttons)

@Verify
@IsState(states = ['setting', 'gaming'])
def CheckRole(user_id=None, data=None):
    idx = data.player.index(user_id)
    role = data.role[idx]
    seat = data.seat[idx]
    txt = '你是：'+role+'/座位：'+str(seat)
    return TextSendMessage(text=txt)

@Verify
@IsState(states = ['setting', 'gaming'])
def CheckCard(user_id=None, data=None):
    idx = data.player.index(user_id)
    seat = data.seat[idx]
    c = Counter(data.playercard[seat])
    txt = '第'+str(data.round)+'輪\n'+'安全引線:'+str(c['安全引線'])+'\n解除引線:'+str(c['解除引線'])+'\n炸彈:'+str(c['炸彈'])
    return TextSendMessage(text=txt)

@Verify
@IsState(states = ['setting'])
def InitScissors(user_id=None, data=None):
    data.state = 'gaming'
    n = len(data.player)
    import random as r
    num = r.randint(1, n)
    data.scissors = num
    txt = '由'+str(num)+'號開始\n點擊你想剪掉誰的引線'

    item = []
    for s in sorted(data.seat):
        if s != data.scissors:
            item.append(
                QuickReplyButton(action=PostbackAction(label=str(s), data=str(s)))
            )
    quickReply = QuickReply(
        items = item
    )
    return TextSendMessage(text=txt, quick_reply=quickReply)

@VerifyChoosePlayer
@IsState(states=['gaming'])
def ChoosePlayer(msg=None, user_id=None, data=None):
    playercard = data.playercard[msg]
    data.nextplayerseat = msg
    return RenderImage(playercard)

@VerifyChooseCard
@IsState(states=['gaming'])
def ChooseCard(msg=None, user_id=None, data=None):
    if ref(msg, data) == 3:
        return TextSendMessage(text='剪到炸彈\n遊戲結束，紅軍獲勝')
    elif ref(msg, data) == 2:
        return TextSendMessage(text='未剪除所有解除引線\n遊戲結束，紅軍獲勝')
    elif ref(msg, data) == 1:
        return TextSendMessage(text='剪除所有解除引線\n遊戲結束，藍軍獲勝')
    else:
        data.playercard[data.nextplayerseat].remove(msg)
        data.allcard.remove(msg)
        data.cutcard.append(msg)
        data.scissors = data.nextplayerseat
        data.times += 1
        n = len(data.player)
        if data.times < n:
            txt = msg+'\n換'+str(data.scissors)+'號點擊你想剪掉誰的引線\n'
            txt += '本輪還剩'+str(n-data.times)+'次剪除機會(第'+str(data.round)+'輪)'

            item = []
            for s in sorted(data.seat):
                if s != data.scissors:
                    item.append(
                        QuickReplyButton(action=PostbackAction(label=str(s), data=str(s)))
                    )
            quickReply = QuickReply(
                items = item
            )
            return TextSendMessage(text=txt, quick_reply=quickReply)
        else:
            data.round += 1
            data.times = 0
            shuffle(data.allcard)
            cnum = 6-data.round #下一輪開始每個人的牌數
            for user in data.player:
                idx = data.player.index(user)
                seat = data.seat[idx]
                data.playercard[seat] = data.allcard[seat*cnum-cnum:seat*cnum]
            c = Counter(data.cutcard)
            txt = msg+'\n已剪除'+str(c['解除引線'])+'張解除引線'
            txt += "\n已重新發牌，請私訊點擊'看牌'"
            buttons = ButtonsTemplate(
                title = '本輪結束',
                text = txt,
                actions = [
                    PostbackTemplateAction(
                        label = '下一輪',
                        data = '下一輪'
                        ),
                ]
            )
            return TemplateSendMessage(alt_text="請私訊點擊'看牌'", template=buttons)
@Verify
@IsState(states = ['gaming'])
def NextRound(user_id=None, data=None):
    txt = '由'+str(data.scissors)+'號開始\n點擊你想剪掉誰的引線'

    item = []
    for s in sorted(data.seat):
        if s != data.scissors:
            item.append(
                QuickReplyButton(action=PostbackAction(label=str(s), data=str(s)))
            )
    quickReply = QuickReply(
        items = item
    )
    return TextSendMessage(text=txt, quick_reply=quickReply)

def CloseGame(data=None):
    data.reset()
    return TextSendMessage(text='房間關閉')
# 處理回傳
@handler.add(PostbackEvent)
def handle_postback(event):
    msg = event.postback.data
    user_id = event.source.user_id
    if msg == '人數':
        message = PlayNum(data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg == '開始':
        message = StartGame(data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg == '身分':
        message = CheckRole(user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg == '看牌':
        message = CheckCard(user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg == '發剪刀':
        message = InitScissors(user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg in [str(i) for i in data.seat]:
        message = ChoosePlayer(msg=int(msg), user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg in ['安全引線', '解除引線', '炸彈']:
        message = ChooseCard(msg=msg, user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg == '下一輪':
        message = NextRound(user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    user_id = event.source.user_id

    if msg == '開房':
        message = CreateGame(data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg in ['++', '+', '+1', '加加', '加']:
        message = PlayOne(user_id=user_id, data=data)
        line_bot_api.reply_message(event.reply_token, message)

    if msg == '關閉':
        message = CloseGame(data=data)
        line_bot_api.reply_message(event.reply_token, message)

import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# git add .
# git commit -m "a"
# git push heroku master
