from langchain_core.runnables import ensure_config

from app.chain_config_base import ChainConfigBase

THREAD_ID = "thread_id"
ACCESS_TOKEN = "access_token"


class ChainConfig(ChainConfigBase):
    def __init__(self):
        super().__init__({})


class ChainConfigEnsure(ChainConfigBase):

    def __init__(self):
        super().__init__(ensure_config())

