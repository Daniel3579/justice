from unittest.mock import patch, MagicMock
from langchain_core.prompts import ChatPromptTemplate
import llm

PROMPT = ChatPromptTemplate.from_messages([("human", "{x}")])

@patch("llm._post")
def test_chat_strips_think(mock_post):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"message": {"content": "<think>думаю</think>Ответ"}}
    mock_post.return_value = resp
    assert llm.chat(PROMPT, {"x": "hi"}) == "Ответ"

@patch("llm._post")
def test_chat_raises_on_error(mock_post):
    mock_post.return_value = MagicMock(status_code=500, text="boom")
    import pytest
    with pytest.raises(llm.LLMError):
        llm.chat(PROMPT, {"x": "hi"})