from typing import AsyncIterator
import aiofiles
import tempfile
import os
from Bio.PDB import PDBParser
from .base import BaseLoader, RawDocument


class PDBLoader(BaseLoader):
    def __init__(self):
        super().__init__("pdb")
        self.parser = PDBParser(QUIET=True)

    async def load(self, path: str, **kwargs) -> AsyncIterator[RawDocument]:
        async with aiofiles.open(path, 'r') as f:
            content = await f.read()

        # BioPython PDBParser 需要文件路径，写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdb', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            structure = self.parser.get_structure("protein", tmp_path)
            model = structure[0]

            metadata = {
                "pdb_id": structure.header.get("idcode", "unknown"),
                "num_chains": len(list(model.get_chains())),
                "num_residues": len(list(model.get_residues())),
                "resolution": structure.header.get("resolution", None)
            }

            for chain in model.get_chains():
                chain_atoms = [(a.coord.tolist(), a.element) for a in chain.get_atoms()]
                yield RawDocument(
                    doc_id=f"pdb_{metadata['pdb_id']}_{chain.id}",
                    source_type="pdb",
                    raw_content={
                        "coordinates": [a[0] for a in chain_atoms],
                        "elements": [a[1] for a in chain_atoms],
                        "sequence": "".join([r.resname for r in chain.get_residues()])
                    },
                    metadata={**metadata, "chain_id": chain.id},
                    file_path=path
                )
        finally:
            os.unlink(tmp_path)
