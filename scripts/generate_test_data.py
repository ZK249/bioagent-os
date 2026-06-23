#!/usr/bin/env python3
import random
import csv
from pathlib import Path

random.seed(42)
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

MOTIFS = {
    "TATA_box": "TATAAA",
    "CAAT_box": "CCAAT",
    "GC_box": "GGCGGG",
    "Kozak": "GCCGCCAUG",
    "PolyA": "AATAAA",
    "P53": "RRRCWWGYYY"
}

SPECIES = [
    "Homo_sapiens", "Mus_musculus", "Drosophila_melanogaster",
    "Arabidopsis_thaliana", "Saccharomyces_cerevisiae",
    "Escherichia_coli", "Caenorhabditis_elegans"
]

def generate_fasta():
    lines = []
    for i in range(12):
        species = random.choice(SPECIES)
        length = random.randint(500, 1500)
        seq = "".join(random.choices("ATCG", k=length))
        
        # 插入真实 Motif
        if random.random() < 0.3:
            motif_name = random.choice(list(MOTIFS.keys()))
            motif_seq = "".join([c for c in MOTIFS[motif_name] if c in "ATCG"])
            if len(motif_seq) >= 4:
                pos = random.randint(50, min(300, length - len(motif_seq)))
                seq = seq[:pos] + motif_seq + seq[pos+len(motif_seq):]
        
        lines.append(f">seq_{i+1}|{species}|promoter_region")
        lines.append(seq)
    
    (DATA_DIR / "demo_sequences.fasta").write_text("\n".join(lines))
    print(f"Generated: 12 FASTA sequences")

def generate_pdb():
    for idx in range(3):
        atoms = []
        resnames = random.choices(
            ["ALA", "VAL", "LEU", "ILE", "PHE", "SER", "THR", "TYR", "GLY", "PRO"],
            k=random.randint(30, 100)
        )
        x, y, z = 0.0, 0.0, 0.0
        atom_idx = 1
        
        for res_idx, resname in enumerate(resnames, 1):
            for atom_name in ["N", "CA", "C"]:
                atoms.append(
                    f"ATOM  {atom_idx:5d}  {atom_name:3s} {resname:3s} A{res_idx:4d}    "
                    f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           {atom_name[0]:1s}"
                )
                x += 3.8
                atom_idx += 1
        
        header = [
            f"HEADER    TEST PROTEIN {idx+1}",
            f"REMARK   2 RESOLUTION.    {random.uniform(1.5, 3.5):.2f} ANGSTROMS."
        ]
        (DATA_DIR / f"demo_structure_{idx+1}.pdb").write_text("\n".join(header + atoms) + "\nEND\n")
    
    print(f"Generated: 3 PDB structures")

def generate_csv():
    header = ["cell_id", "gene_expression", "cell_type", "cluster", "species"]
    rows = []
    cell_types = ["T_cell", "B_cell", "Monocyte", "NK_cell", "Macrophage", 
                  "Neuron", "Fibroblast", "Hepatocyte"]
    
    for i in range(20):
        rows.append([
            f"cell_{i:03d}",
            round(random.uniform(0, 15), 2),
            random.choice(cell_types),
            random.randint(0, 10),
            random.choice(SPECIES)
        ])
    
    with open(DATA_DIR / "demo_expression.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Generated: 20 CSV expression records")

if __name__ == "__main__":
    generate_fasta()
    generate_pdb()
    generate_csv()
    print("\nAll test data generated successfully!")