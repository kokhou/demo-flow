import os

from pydantic.v1 import BaseSettings


def get_db_url() -> str:
    return "postgresql+psycopg2://{0}:{1}@{2}/{3}".format(
        "postgres",
        "postgres",
        "host.docker.internal:5432",  # "localhost:5432",
        "ai-engine",
    )


class Settings(BaseSettings):
    PROJECT_NAME: str

    # API Documentation
    OPEN_API_URL: str = "/openapi.json"
    DOCS_URL: str = "/"

    # API Configuration
    API_V1_STR: str = "/api/v1"

    # DB Configuration
    SQLALCHEMY_DATABASE_URI: str = get_db_url()

    # OpenAi API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "here")
    default_embedding_model = "text-embedding-3-small"
    default_model = (
        "gpt-3.5-turbo-1106"  # $0.0005 / 1K tokens	$0.0015 / 1K tokens / window 16k
    )

    # TODO change your db path
    db_path = '/Users/choikokhou/Documents/workspace/sl/engine/model_rnd/app/core.db'

    INSTRUCTION = (
        "You are a knowledgeable customer service representative for MyTHEO. Your role is to provide accurate information based on the provided details. If a question arises that you cannot answer using the available information, you should clearly communicate this to the user. Reply in human way and use paragraphs and format to markdown.")


settings = Settings(PROJECT_NAME="ai-engine")
