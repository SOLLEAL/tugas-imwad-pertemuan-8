#!/usr/bin/env python3
"""Audit dataset citra kendaraan: validasi, hash duplikat, rekap, dan split manifest."""
from __future__ import annotations

import argparse
import csv
import hashlib
import random
from collections import defaultdict
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Dependensi Pillow belum terpasang. Jalankan: python -m pip install Pillow") from exc

CLASSES = ["mobil", "sepeda_motor", "bus", "truk"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
SPLIT_RATIOS = (("train", 0.70), ("validation", 0.15), ("test", 0.15))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def split_items(items: list[dict], seed: int) -> list[dict]:
    """Bagi satu kelas secara deterministik dengan rasio 70:15:15."""
    ordered = sorted(items, key=lambda item: item["relative_path"].lower())
    random.Random(seed).shuffle(ordered)
    n = len(ordered)
    n_train = int(n * 0.70)
    n_val = int(n * 0.15)
    # Pastikan semua item teralokasi; sisa pembulatan masuk test.
    assignments = (
        [("train", item) for item in ordered[:n_train]]
        + [("validation", item) for item in ordered[n_train:n_train + n_val]]
        + [("test", item) for item in ordered[n_train + n_val:]]
    )
    return [{"relative_path": item["relative_path"], "class": item["class"],
             "sha256": item["sha256"], "split": split}
            for split, item in assignments]


def audit(input_dir: Path, output_dir: Path, seed: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []
    hash_groups: dict[str, list[dict]] = defaultdict(list)
    corrupt_rows: list[dict] = []

    for class_name in CLASSES:
        class_dir = input_dir / class_name
        if not class_dir.exists():
            print(f"[PERINGATAN] Folder kelas tidak ditemukan: {class_dir}")
            continue

        files = sorted(
            (p for p in class_dir.rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS),
            key=lambda p: str(p).lower()
        )
        for path in files:
            relative_path = path.relative_to(input_dir).as_posix()
            row = {
                "relative_path": relative_path,
                "class": class_name,
                "extension": path.suffix.lower(),
                "bytes": path.stat().st_size,
                "sha256": "",
                "image_status": "valid",
                "duplicate_group": "",
                "duplicate_status": "unique",
                "split": "",
            }
            try:
                with Image.open(path) as image:
                    image.verify()
                # Reopen and fully decode to catch files that verify() alone may miss.
                with Image.open(path) as image:
                    image.load()
                    if image.width <= 0 or image.height <= 0:
                        raise ValueError("Dimensi gambar tidak valid")
                row["sha256"] = sha256_file(path)
                hash_groups[row["sha256"]].append(row)
            except Exception as exc:
                row["image_status"] = f"corrupt: {type(exc).__name__}: {exc}"
                corrupt_rows.append({
                    "relative_path": relative_path,
                    "class": class_name,
                    "error": row["image_status"],
                })
            all_rows.append(row)

    within_class_rows: list[dict] = []
    cross_class_rows: list[dict] = []
    ambiguous_hashes: set[str] = set()
    duplicate_hashes: set[str] = set()

    for digest, group in sorted(hash_groups.items()):
        if len(group) < 2:
            continue
        duplicate_hashes.add(digest)
        classes = sorted({row["class"] for row in group})
        group_id = digest[:12]
        for row in group:
            row["duplicate_group"] = group_id
        if len(classes) > 1:
            ambiguous_hashes.add(digest)
            for row in group:
                row["duplicate_status"] = "cross_class_review"
                cross_class_rows.append({
                    "duplicate_group": group_id,
                    "sha256": digest,
                    "relative_path": row["relative_path"],
                    "class": row["class"],
                    "classes_in_group": ";".join(classes),
                    "action": "Periksa label; grup dikeluarkan dari split sementara",
                })
        else:
            # Keep first sorted path as representative; mark remaining copies.
            group_sorted = sorted(group, key=lambda row: row["relative_path"].lower())
            representative = group_sorted[0]
            representative["duplicate_status"] = "representative_within_class"
            for duplicate in group_sorted[1:]:
                duplicate["duplicate_status"] = "duplicate_within_class_excluded"
            for row in group_sorted:
                within_class_rows.append({
                    "duplicate_group": group_id,
                    "sha256": digest,
                    "relative_path": row["relative_path"],
                    "class": row["class"],
                    "representative_path": representative["relative_path"],
                    "duplicate_status": row["duplicate_status"],
                })

    eligible_by_class: dict[str, list[dict]] = defaultdict(list)
    for row in all_rows:
        if row["image_status"] != "valid":
            row["split"] = "excluded_corrupt"
            continue
        if row["sha256"] in ambiguous_hashes:
            row["split"] = "excluded_cross_class_duplicate"
            continue
        if row["duplicate_status"] == "duplicate_within_class_excluded":
            row["split"] = "excluded_within_class_duplicate"
            continue
        eligible_by_class[row["class"]].append(row)

    split_rows: list[dict] = []
    for class_index, class_name in enumerate(CLASSES):
        class_splits = split_items(eligible_by_class[class_name], seed + class_index)
        split_rows.extend(class_splits)
        assignment = {item["relative_path"]: item["split"] for item in class_splits}
        for row in eligible_by_class[class_name]:
            row["split"] = assignment[row["relative_path"]]

    summary_rows = []
    for class_name in CLASSES:
        class_rows = [row for row in all_rows if row["class"] == class_name]
        summary_rows.append({
            "class": class_name,
            "total_images": len(class_rows),
            "valid_images": sum(r["image_status"] == "valid" for r in class_rows),
            "corrupt_images": sum(r["image_status"] != "valid" for r in class_rows),
            "within_class_duplicate_copies_excluded": sum(r["duplicate_status"] == "duplicate_within_class_excluded" for r in class_rows),
            "cross_class_duplicate_files": sum(r["duplicate_status"] == "cross_class_review" for r in class_rows),
            "eligible_unique_images": len(eligible_by_class[class_name]),
            "train": sum(r["split"] == "train" for r in class_rows),
            "validation": sum(r["split"] == "validation" for r in class_rows),
            "test": sum(r["split"] == "test" for r in class_rows),
        })

    write_csv(output_dir / "detail_audit.csv",
              ["relative_path", "class", "extension", "bytes", "sha256", "image_status",
               "duplicate_group", "duplicate_status", "split"], all_rows)
    write_csv(output_dir / "rekap_dataset.csv",
              ["class", "total_images", "valid_images", "corrupt_images",
               "within_class_duplicate_copies_excluded", "cross_class_duplicate_files",
               "eligible_unique_images", "train", "validation", "test"], summary_rows)
    write_csv(output_dir / "duplikat_dalam_kelas.csv",
              ["duplicate_group", "sha256", "relative_path", "class",
               "representative_path", "duplicate_status"], within_class_rows)
    write_csv(output_dir / "duplikat_lintas_kelas.csv",
              ["duplicate_group", "sha256", "relative_path", "class", "classes_in_group", "action"],
              cross_class_rows)
    write_csv(output_dir / "file_corrupt.csv",
              ["relative_path", "class", "error"], corrupt_rows)
    write_csv(output_dir / "pembagian_dataset.csv",
              ["relative_path", "class", "sha256", "split"], split_rows)

    print("\n=== AUDIT DATASET CITRA KENDARAAN ===")
    print(f"Folder input       : {input_dir}")
    print(f"Folder output      : {output_dir}")
    print(f"Total gambar       : {len(all_rows)}")
    print(f"Gambar rusak       : {len(corrupt_rows)}")
    print(f"Grup hash duplikat : {len(duplicate_hashes)}")
    print(f"Grup lintas kelas  : {len(ambiguous_hashes)}")
    print("\nRekap per kelas:")
    for row in summary_rows:
        print(f"- {row['class']}: total={row['total_images']}, layak={row['eligible_unique_images']}, "
              f"train={row['train']}, validation={row['validation']}, test={row['test']}")
    print("\nSelesai. Periksa hasil CSV, khususnya duplikat lintas kelas sebelum melatih model.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit dataset citra kendaraan.")
    parser.add_argument("--input", type=Path, default=Path("dataset_raw"),
                        help="Folder dataset dengan subfolder kelas (default: dataset_raw)")
    parser.add_argument("--output", type=Path, default=Path("hasil_audit"),
                        help="Folder hasil audit (default: hasil_audit)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Seed pembagian dataset agar hasil konsisten (default: 42)")
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Folder input tidak ditemukan: {args.input}")
    audit(args.input, args.output, args.seed)


if __name__ == "__main__":
    main()
