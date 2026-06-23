from typing import AsyncIterator
import aiofiles
from Bio import SeqIO
from io import StringIO
from .base import BaseLoader, RawDocument

class FastaLoader(BaseLoader):
    def __init__(self):
        super().__init__("fasta")
    
    async def load(self, path: str, **kwargs) -> AsyncIterator[RawDocument]:
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()
        
        # SeqIO需要同步解析，但IO已经是异步的
        records = list(SeqIO.parse(StringIO(content), "fasta"))
        
        for idx, record in enumerate(records):
            metadata = {
                "species": kwargs.get("species", "unknown"),
                "seq_length": len(record.seq),
                "description": record.description,
                "chunk_idx": idx
            }

            raw_id = f"fasta_{record.id}_{idx}"
            doc_id = raw_id[:100] if len(raw_id) > 100 else raw_id

            yield RawDocument(
                doc_id=doc_id,
                source_type="fasta",
                raw_content=str(record.seq),
                metadata=metadata,
                file_path=path
            )