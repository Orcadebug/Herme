"""

 .env
"""

import os
from dotenv import load_dotenv

#  .env
# : Hermes/.env ( backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    #  .env
    load_dotenv(override=True)


class Config:
    """Flask"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    # JSON - ASCII \uXXXX
    JSON_AS_ASCII = False

    # LLMOpenAI
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME')

    # Zep
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')

    # Sports public data configuration
    SPORTS_DATA_BASE_URL = os.environ.get('SPORTS_DATA_BASE_URL')
    SPORTS_DATA_API_KEY = os.environ.get('SPORTS_DATA_API_KEY')

    # Sports research configuration
    # This is intentionally separate from the main LLM runtime.
    # Research gathers live information, while planning/simulation/reporting use LLM_*.
    SPORTS_RESEARCH_API_KEY = os.environ.get('SPORTS_RESEARCH_API_KEY')
    SPORTS_RESEARCH_BASE_URL = os.environ.get('SPORTS_RESEARCH_BASE_URL')
    SPORTS_RESEARCH_MODEL_NAME = os.environ.get('SPORTS_RESEARCH_MODEL_NAME')

    #
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    #
    DEFAULT_CHUNK_SIZE = 500  #
    DEFAULT_CHUNK_OVERLAP = 50  #

    # OASIS
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # OASIS
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def validate(cls):
        """"""
        errors = []

        if not cls.SECRET_KEY or cls.SECRET_KEY in {'hermes-secret-key', 'change-me', 'change_me'}:
            errors.append('SECRET_KEY ')

        if cls.DEBUG:
            errors.append('FLASK_DEBUG  False ')

        if not cls.LLM_API_KEY:
            errors.append('LLM_API_KEY ')

        if not cls.LLM_BASE_URL:
            errors.append('LLM_BASE_URL ')
        elif not str(cls.LLM_BASE_URL).startswith('https://'):
            errors.append('LLM_BASE_URL  HTTPS')

        if not cls.LLM_MODEL_NAME:
            errors.append('LLM_MODEL_NAME ')

        if not cls.SPORTS_RESEARCH_API_KEY:
            errors.append('SPORTS_RESEARCH_API_KEY ')

        if not cls.SPORTS_RESEARCH_BASE_URL:
            errors.append('SPORTS_RESEARCH_BASE_URL ')
        elif not str(cls.SPORTS_RESEARCH_BASE_URL).startswith('https://'):
            errors.append('SPORTS_RESEARCH_BASE_URL  HTTPS')

        if not cls.SPORTS_RESEARCH_MODEL_NAME:
            errors.append('SPORTS_RESEARCH_MODEL_NAME ')

        return errors
