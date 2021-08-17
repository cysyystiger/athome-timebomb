#這些是LINE官方開放的套件組合透過import來套用這個檔案上
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

def RenderImage(playercard):
    images = TemplateSendMessage(
        alt_text='點擊想剪除的引線',
        template=ImageCarouselTemplate(
            columns=[
                ImageCarouselColumn(
                    image_url="https://i01piccdn.sogoucdn.com/5c15b5d76239f527",
                    action=PostbackTemplateAction(
                        label="?",
                        data=s
                    )
                ) for s in playercard
            ]
        )
    )
    return images
