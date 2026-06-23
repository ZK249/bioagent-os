#!/usr/bin/env python3
"""
下载真实生物数据用于模块A测试
- NCBI Entrez API: 真实FASTA序列（TP53基因，人类，500-1000bp）
- RCSB PDB API: 真实蛋白质结构（经典小分子蛋白）
限制数据量以保证 16GB 内存安全。
"""

import requests
import time
import re
from pathlib import Path

DATA_DIR = Path("data/real")
DATA_DIR.mkdir(exist_ok=True)

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def format_fasta_header(raw_header: str, idx: int) -> str:
    """将NCBI原始header转为项目标准格式: >doc_id|species|description"""
    line = raw_header.lstrip(">").strip()
    
    # 简单物种识别
    species = "unknown"
    if "Homo sapiens" in line:
        species = "Homo_sapiens"
    elif "Mus musculus" in line:
        species = "Mus_musculus"
    elif "Rattus norvegicus" in line:
        species = "Rattus_norvegicus"
    
    doc_id = f"ncbi_{idx:03d}"
    # 清理描述，去掉gi/ref等ID，保留基因描述
    desc = re.sub(r'gi\|\d+\|ref\|[^\|]+\|\s*', '', line)
    desc = re.sub(r'\s+', '_', desc)[:100]
    
    return f">{doc_id}|{species}|{desc}"


def download_ncbi_fasta(query="Homo sapiens[ORGN] AND TP53[GENE] AND 500:1000[SLEN]", retmax=15):
    """从NCBI下载真实FASTA序列"""
    print(f"🔍 NCBI Search: {query}")
    
    # Step 1: esearch 获取ID列表
    search_url = f"{NCBI_BASE}/esearch.fcgi"
    r = requests.get(search_url, params={
        "db": "nucleotide", "term": query, "retmode": "json", "retmax": retmax
    }, timeout=30)
    r.raise_for_status()
    id_list = r.json().get("esearchresult", {}).get("idlist", [])
    print(f"   Found {len(id_list)} records")
    
    if not id_list:
        print("   ⚠️ No records found. Skip FASTA.")
        return None
    
    # Step 2: efetch 获取FASTA文本（分批，遵守NCBI rate limit）
    all_lines = []
    batch_size = 10
    seq_idx = 0
    
    for i in range(0, len(id_list), batch_size):
        batch = id_list[i:i+batch_size]
        print(f"   Fetching batch {i//batch_size + 1}/{(len(id_list)-1)//batch_size + 1} ...")
        
        r = requests.get(f"{NCBI_BASE}/efetch.fcgi", params={
            "db": "nucleotide", "id": ",".join(batch),
            "rettype": "fasta", "retmode": "text"
        }, timeout=60)
        r.raise_for_status()
        
        # 格式化每一条FASTA记录
        raw_text = r.text
        records = raw_text.split(">")
        for rec in records:
            if not rec.strip():
                continue
            lines = rec.strip().split("\n")
            header = ">" + lines[0]
            sequence = "".join(lines[1:])
            
            formatted_header = format_fasta_header(header, seq_idx)
            all_lines.append(formatted_header)
            all_lines.append(sequence)
            seq_idx += 1
        
        time.sleep(0.6)  # NCBI rate limit: max 3 req/sec without API key
    
    # Step 3: 保存
    output = DATA_DIR / "real_sequences.fasta"
    with open(output, "w") as f:
        f.write("\n".join(all_lines))
    
    print(f"   ✅ Saved: {output} ({seq_idx} sequences)")
    return output


def download_rcsb_pdb(pdb_ids=None, max_count=5):
    """从RCSB PDB下载真实结构文件"""
    if pdb_ids is None:
        # 经典蛋白结构：肌红蛋白、泛素、溶菌酶、血红蛋白、黄瓜病毒
        pdb_ids = ["1MBN", "1UBQ", "2LZM", "4HHB", "1CRN"]
    pdb_ids = pdb_ids[:max_count]
    
    pdb_dir = DATA_DIR / "pdb"
    pdb_dir.mkdir(exist_ok=True)
    
    print(f"🔍 RCSB PDB: downloading {len(pdb_ids)} structures...")
    downloaded = []
    
    for pid in pdb_ids:
        url = f"https://files.rcsb.org/download/{pid}.pdb"
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            out_path = pdb_dir / f"{pid}.pdb"
            with open(out_path, "w") as f:
                f.write(r.text)
            downloaded.append(str(out_path))
            print(f"   ✅ {pid}.pdb  ({len(r.text)//1024} KB)")
            time.sleep(0.3)
        except Exception as e:
            print(f"   ❌ {pid}.pdb failed: {e}")
    
    print(f"   Downloaded: {len(downloaded)}/{len(pdb_ids)}")
    return downloaded


if __name__ == "__main__":
    print("=" * 60)
    print("Real Bio Data Downloader")
    print("=" * 60)
    
    # 15条真实FASTA（TP53相关，长度500-1000bp，安全）
    download_ncbi_fasta(
        query="Homo sapiens[ORGN] AND TP53[GENE] AND 500:1000[SLEN]",
        retmax=15
    )
    
    # 5个真实PDB结构
    download_rcsb_pdb(max_count=5)
    
    print("\n" + "=" * 60)
    print("✅ Done. Files saved to data/real/")
    print("Next: python scripts/ingest_real_data.py")
    print("=" * 60)