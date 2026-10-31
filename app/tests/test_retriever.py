from unittest.mock import patch, MagicMock
import retriever

@patch("retriever.load_chroma_db")
def test_retriever_singleton(mock_load):
    db = MagicMock()
    db.as_retriever.return_value = "R"
    mock_load.return_value = db

    retriever._db = None  # сброс кэша
    r1 = retriever.get_local_retriever()
    r2 = retriever.get_local_retriever()
    assert r1 is r2 is "R"
    mock_load.assert_called_once()