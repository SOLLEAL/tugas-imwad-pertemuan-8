# Laporan Audit Dataset Citra Kendaraan

## 1. Tujuan
Mengevaluasi kualitas dataset citra kendaraan sebelum digunakan untuk klasifikasi empat kelas: mobil, sepeda motor, bus, dan truk.

## 2. Data dan prosedur
Dataset harus ditempatkan pada folder `dataset_raw/`. Skrip `audit_dataset.py` memeriksa keterbacaan gambar, membuat hash SHA-256, mengelompokkan duplikat, dan menyusun manifest split 70:15:15.

## 3. Hasil
**Belum tersedia.** Laporan ini adalah templat. Isi hasil setelah menjalankan `python audit_dataset.py` pada dataset yang sebenarnya. Gunakan angka dari `hasil_audit/rekap_dataset.csv`; jangan menggunakan angka perkiraan sebagai hasil penelitian.

## 4. Pembahasan
Jelaskan proporsi file rusak, duplikat dalam kelas, duplikat lintas kelas, dan distribusi jumlah data train/validation/test. Tinjau secara manual grup duplikat lintas kelas sebelum memutuskan label yang benar.

## 5. Kesimpulan
Kesimpulan baru dapat dibuat setelah audit dijalankan pada dataset yang digunakan. Dokumentasikan nama dataset, sumber, tanggal akses, dan lisensinya.
