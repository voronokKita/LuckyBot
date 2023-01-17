""" pyTelegramBotAPI update handlers. """

import logging
from logs import console, event
logger = logging.getLogger(__name__)

from lucky_bot.bot_init import BOT

'''
Case 1
/start -> responder -> 'hello message'

Case 2
/help -> responder -> 'help message'

Case 3
/add -> responder -> 'invitation message'
text -> parser insert data -> 'OK or ERROR message'

Case 4
/list -> responder select data -> 'list message'

Case 5
/note [n] > responder select data -> 'text message'

Case 6
/delete [n, n+1] -> responder delete data -> 'OK or ERROR message'

Case exception
some text or wrong command -> responder -> 'help message'

Case exception
some command after add/ -> execute command

Case sender exception
/delete_user -> responder delete user
'''
