from raglab.core.registry import create
from raglab.core.types import Document


def test_recursive_chunker_respects_size():
    text = ". ".join(f"sentence number {i} with some filler words" for i in range(200))
    chunker = create("chunker", "recursive", chunk_size=200, overlap=20)
    chunks = chunker.chunk([Document(text=text, metadata={"source": "t"})])
    assert len(chunks) > 1
    # overlap means chunks can slightly exceed size; allow a margin
    assert all(len(c.text) <= 200 + 40 for c in chunks)
    assert all(c.document_id for c in chunks)


def test_parent_child_carries_parent_text():
    text = "\n\n".join(f"paragraph {i} " * 30 for i in range(5))
    chunker = create("chunker", "parent_child", chunk_size=800, child_size=200)
    chunks = chunker.chunk([Document(text=text, metadata={"source": "t"})])
    assert chunks
    assert any("parent_text" in c.metadata for c in chunks)
