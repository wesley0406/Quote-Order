
channel_access_token = 'KKP6lxqEpBaBTbz7EmkxDW/H+1D1L++WHImL7uO9ArPBrTEPn634dI0Z5hVYp45fwJfBWpWHqqNTMLalsB2naKENDleaI8RbvcOPHn4wXmSR96ldio4KA277+5He3BOrbn2coRtjoP/2Cw4BLZuF1AdB04t89/1O/w1cDnyilFU='
channel_secret = "7b5bf19c73843019914c80a6ec4f3aa2"

from linebot import LineBotApi
from linebot.models import TextSendMessage

# Replace with your Channel Access Token
line_bot_api = LineBotApi(channel_access_token )

# Replace with your User ID (or group ID)
user_id = "wesley870406"

# Fixed message
message = TextSendMessage(text='Hello! This is your daily reminder.')

# Send the message
line_bot_api.push_message(user_id, message)
