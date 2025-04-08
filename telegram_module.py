from telegram import Bot
import asyncio
import logging

class TelegramBot:
    def __init__(self, token):
        self.bot = Bot(token)
        self.logger = logging.getLogger(__name__)

    def send_message(self, chat_id, message):
        try:
            # Run async send_message in sync context
            async def send():
                await self.bot.send_message(chat_id=chat_id, text=message)
            
            # Create event loop if there isn't one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(send())
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False
