from config import Var, LOGS
from helper.anime_utils import sendMessage

class Reporter:
    def __init__(self, client=None):
        self.client = client

    async def report(self, text, type="info", log=True, client=None):
        if log:
            if type == "error":
                LOGS.error(text)
            elif type == "warning":
                LOGS.warning(text)
            else:
                LOGS.info(text)

        target_client = client or self.client
        if target_client:
            log_ch = getattr(target_client, 'log_channel', Var.LOG_CHANNEL)
            await sendMessage(target_client, log_ch, f"[{type.upper()}] {text}")

rep = Reporter()
