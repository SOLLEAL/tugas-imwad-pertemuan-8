# Metodologi Audit Dataset

## Tahapan
1. **Inventarisasi**: membaca file gambar dari folder masing-masing kelas kendaraan.
2. **Validasi file**: membuka, memverifikasi, dan mendekode gambar untuk menemukan file yang rusak/tidak terbaca.
3. **Deteksi duplikat**: menghitung SHA-256 dari byte file. Hash sama menunjukkan file identik secara byte.
4. **Pemeriksaan label**: duplikat lintas kelas ditandai sebagai ambigu untuk pemeriksaan manual.
5. **Pembersihan**: file rusak, salinan duplikat dalam kelas, dan grup duplikat lintas kelas tidak dimasukkan ke split.
6. **Pembagian data**: gambar valid yang tersisa dibagi per kelas menjadi train 70%, validation 15%, dan test 15%, dengan seed 42.

## Batasan
Hash tidak mendeteksi gambar yang sama secara visual jika byte file berbeda. Pemeriksaan kemiripan visual dapat ditambahkan kemudian menggunakan perceptual hash (pHash) atau embedding citra.
