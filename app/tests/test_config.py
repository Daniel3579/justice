from pathlib import Path
import config

def test_paths_are_absolute():
    assert Path(config.APP_DB_PATH).is_absolute()
    assert Path(config.CHROMA_DB_PATH).is_absolute()

def test_limits_positive():
    assert config.MAX_MESSAGE_CHARS > 0
    assert config.MIN_PASSWORD_LENGTH >= 6
    assert config.TOP_K_LOCAL > 0