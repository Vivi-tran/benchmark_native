from pathlib import Path
import re, shutil
import urllib.request
import urllib.error
import argparse
from typing import Optional
import pandas as pd


def download(pdb_id: str, out_dir: str | Path = ".") -> Path:
    """
    Download a .pdb file from RCSB by PDB ID.

    pdb_id : str
        4-character PDB accession (case-insensitive), e.g., "1CRN".
    out_dir : str or Path, default "."
        Directory to save into (created if missing).
    Returns None.

    """
    if not re.fullmatch(r"[0-9A-Za-z]{4}", pdb_id or ""):
        raise ValueError(f"Invalid PDB ID: {pdb_id!r}")

    pdb_id = pdb_id.upper()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target = out_dir / f"{pdb_id}.pdb"
    if target.exists():
        pass

    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    tmp = target.with_suffix(".pdb.part")

    try:
        with urllib.request.urlopen(url) as resp, open(tmp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        tmp.replace(target)

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(f"PDB entry {pdb_id} not found at RCSB.") from e
        raise


def retrieve_natives(input: str, outdir: str | Path = ".") -> Path:
    """
    Retrieve native PDB files given a PDB ID or a file containing multiple PDB IDs.

    input : str
        A single PDB ID or a path to a file with multiple PDB IDs (one per line).
    out_dir : str or Path, default "."
        Directory to save into (created if missing).
    Returns Path
        Path to the directory containing downloaded PDB files.

    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    input_path = Path(input)
    if input_path.exists() and input_path.suffix == ".csv":
        df = pd.read_csv(input_path)
        df.dropna(subset=["pdb_id"], inplace=True)
        pdb_ids = df["pdb_id"].tolist()
        try:
            ids = df["id"].tolist()
        except Exception as e:
            df["id"] = df["pdb_id"]
            ids = df["id"].tolist()

    else:
        pdb_ids = [input.strip()]

    for pdb_id, id in zip(pdb_ids, ids):
        download(pdb_id, outdir)
        shutil.move(
            outdir / f"{pdb_id}.pdb",
            outdir / f"{id}.pdb",
        )
    return outdir


def build_download_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download native structures from RCSB by pdbid named as specified."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to input csv file with columns <id>, <pdb_id>.",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        default=".",
        help="Directory to save into. Default: current directory.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="natives",
        help="Name for the downloaded files. Default: natives.",
    )
    return parser


def main():
    parser = build_download_parser()
    args = parser.parse_args()
    output_dir = Path(args.output_dir) / "natives"
    retrieve_natives(args.input, output_dir)
    shutil.copy2(args.input, output_dir / Path(args.input).name)
    return


if __name__ == "__main__":
    main()
