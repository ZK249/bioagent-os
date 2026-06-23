import numpy as np
from typing import Dict, List, Tuple
from Bio.PDB import PDBParser, PPBuilder, DSSP
from Bio.PDB.vectors import calc_dihedral


class StructureProcessor:
    """
    PDB结构预处理：二面角、坐标特征、二级结构
    复用你TDA/RNA结构分析的经验
    """

    def __init__(self):
        self.parser = PDBParser(QUIET=True)

    def extract_backbone(self, chain) -> Dict[str, List]:
        """
        提取主链坐标（N-CA-C）用于后续TDA/距离矩阵计算
        """
        n_coords, ca_coords, c_coords = [], [], []
        residues = []

        for residue in chain.get_residues():
            if residue.get_id()[0] != " ":  # 跳过异构残基（水分子等）
                continue
            try:
                n = residue["N"].get_coord().tolist()
                ca = residue["CA"].get_coord().tolist()
                c = residue["C"].get_coord().tolist()
                n_coords.append(n)
                ca_coords.append(ca)
                c_coords.append(c)
                residues.append(residue.resname)
            except KeyError:
                continue

        return {
            "N": n_coords,
            "CA": ca_coords,
            "C": c_coords,
            "residues": residues,
            "length": len(residues)
        }

    def calc_dihedral_angles(self, chain) -> Dict[str, List[float]]:
        """
        计算phi/psi二面角（Ramachandran plot数据）
        可直接用于你的TDA分析
        """
        builder = PPBuilder()
        peptides = builder.build_peptides(chain)

        phi, psi = [], []
        for peptide in peptides:
            for res in peptide:
                try:
                    phi.append(res.get_phi())
                    psi.append(res.get_psi())
                except Exception:
                    continue

        # 转为角度制，过滤None
        phi_deg = [np.degrees(p) for p in phi if p is not None]
        psi_deg = [np.degrees(p) for p in psi if p is not None]

        return {
            "phi": phi_deg,
            "psi": psi_deg,
            "rama_pairs": list(zip(phi_deg, psi_deg))  # (phi, psi) 对
        }

    def calc_distance_matrix(self, coords: List[List[float]], threshold: float = 8.0) -> np.ndarray:
        """
        计算CA原子距离矩阵，用于TDA/Rips复形
        threshold: 8Å 为常见的残基接触阈值
        """
        coords_arr = np.array(coords)
        diff = coords_arr[:, None, :] - coords_arr[None, :, :]
        dist = np.sqrt(np.sum(diff ** 2, axis=-1))
        return dist

    def contact_map(self, dist_matrix: np.ndarray, threshold: float = 8.0) -> np.ndarray:
        """
        二值接触图（0/1矩阵），可直接作为TDA的输入
        """
        return (dist_matrix < threshold).astype(np.int8)

    def process_chain(self, chain, chain_id: str = "A") -> Dict:
        """
        完整处理一条链，输出结构化文本 + 特征向量
        """
        backbone = self.extract_backbone(chain)
        dihedrals = self.calc_dihedral_angles(chain)

        # 距离矩阵（用于metadata，不直接存入文本）
        if len(backbone["CA"]) > 2:
            dist_mat = self.calc_distance_matrix(backbone["CA"])
            contact = self.contact_map(dist_mat)
            # 提取拓扑特征：接触数、连通分量数（简化版）
            contact_count = int(np.sum(contact) / 2)
        else:
            contact_count = 0

        # 生成结构化文本（用于向量化）
        text = (
            f"Protein chain {chain_id} with {backbone['length']} residues. "
            f"Residue composition: {', '.join(set(backbone['residues']))}. "
            f"Mean phi {np.mean(dihedrals['phi']):.1f} degrees, "
            f"Mean psi {np.mean(dihedrals['psi']):.1f} degrees. "
            f"Contact pairs under 8A: {contact_count}."
        )

        return {
            "text": text,
            "backbone": backbone,
            "dihedrals": dihedrals,
            "contact_count": contact_count,
            "length": backbone["length"]
        }