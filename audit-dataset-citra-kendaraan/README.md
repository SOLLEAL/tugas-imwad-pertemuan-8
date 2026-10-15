# Audit dan Pembersihan Dataset Citra Kendaraan

Proyek ini mengaudit kualitas dataset citra kendaraan sebelum digunakan untuk klasifikasi jenis kendaraan. Struktur dan pendekatan dokumentasinya terinspirasi dari repository referensi [ainunumam/ainunumam](https://github.com/ainunumam/ainunumam), dengan objek penelitian diubah menjadi citra kendaraan.

> **Status:** kerangka proyek siap digunakan. Hasil audit belum tersedia sampai dataset citra kendaraan dimasukkan dan skrip dijalankan. Angka hasil tidak dibuat-buat.

## Tujuan

- Memeriksa apakah berkas gambar dapat dibaca.
- Mendeteksi gambar duplikat identik menggunakan hash SHA-256.
- Memisahkan duplikat dalam kelas dan duplikat lintas kelas untuk pemeriksaan label.
- Membuat rekap jumlah gambar per kelas.
- Membuat manifest pembagian data train, validation, dan test dengan rasio 70:15:15 serta seed 42.

## Kelas dataset

Masukkan gambar ke folder yang sesuai:

- `mobil/`
- `sepeda_motor/`
- `bus/`
- `truk/`

Struktur yang diharapkan:

```text
audit-dataset-citra-kendaraan/
├── README.md
├── README.MD
├── audit_dataset.py
├── dataset_raw/
│   ├── mobil/
│   ├── sepeda_motor/
│   ├── bus/
│   └── truk/
├── hasil_audit/
│   └── .gitkeep
├── laporan/
│   └── Laporan_Audit_Dataset.md
├── doc/
│   └── Metodologi.md
├── functional/
│   └── Kebutuhan_Fungsional.md
└── requirement/
    └── Kebutuhan_Sistem.md
```

Folder dataset sengaja tidak berisi gambar contoh. Gunakan dataset yang diperoleh secara sah dan cantumkan sumber dataset pada laporan tugas.

## Persyaratan

- Python 3.9 atau lebih baru
- Pillow

Instal dependensi:

```bash
python -m pip install Pillow
```

## Cara menjalankan

Jalankan dari folder utama proyek:

```bash
python audit_dataset.py
```

Atau tentukan lokasi dataset dan folder output:

```bash
python audit_dataset.py --input dataset_raw --output hasil_audit --seed 42
```

Setiap kelas harus memiliki subfolder sendiri. Skrip membaca format `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, dan `.tiff`.

## Keluaran audit

Skrip membuat berkas berikut di `hasil_audit/`:

| Berkas | Isi |
|---|---|
| `rekap_dataset.csv` | Ringkasan jumlah file, file valid, rusak, duplikat, dan data yang masuk split per kelas |
| `detail_audit.csv` | Status dan hash setiap gambar |
| `duplikat_dalam_kelas.csv` | Grup gambar duplikat dengan label kelas sama |
| `duplikat_lintas_kelas.csv` | Grup gambar identik yang muncul pada kelas berbeda |
| `file_corrupt.csv` | File gambar yang gagal dibaca |
| `pembagian_dataset.csv` | Manifest gambar unik yang layak digunakan beserta split-nya |

## Aturan pembersihan dan pembagian

1. Setiap gambar diuji menggunakan Pillow.
2. SHA-256 dihitung dari byte file untuk mendeteksi file yang identik.
3. Jika gambar identik muncul pada kelas berbeda, seluruh grup ditandai sebagai ambigu dan tidak dimasukkan ke manifest split sampai label diperiksa.
4. Jika gambar identik muncul lebih dari sekali dalam kelas yang sama, satu file representatif dipertahankan; salinan lainnya ditandai duplikat.
5. Hanya gambar valid dan tidak ambigu yang dibagi ke train, validation, dan test.
6. Pembagian dilakukan per kelas secara deterministik dengan rasio 70:15:15 dan seed 42. Jumlah aktual per split dapat berbeda satu gambar akibat pembulatan.

**Catatan:** hash SHA-256 hanya mendeteksi file identik secara byte. Gambar visual yang sama tetapi telah diubah ukuran, dikompresi ulang, atau diedit mungkin tidak terdeteksi sebagai duplikat.

## Catatan interpretasi

- Hasil audit bergantung pada dataset yang dimasukkan.
- `pembagian_dataset.csv` adalah manifest, bukan salinan gambar ke folder train/validation/test.
- Sebelum melatih model, periksa duplikat lintas kelas dan pastikan label sesuai.
- Jangan menyatakan jumlah gambar atau hasil audit tertentu sebelum skrip dijalankan pada dataset sebenarnya.

## Sumber

- Repository referensi: https://github.com/ainunumam/ainunumam
- Dokumentasi Pillow: https://pillow.readthedocs.io/
