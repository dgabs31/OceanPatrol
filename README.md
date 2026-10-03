# OceanPatrol: SeaTracker Hybrid

Prototipe aplikasi untuk karya infografis "OceanPatrol: Membongkar Titik Kritis Tersembunyi" (Tim IRIS PRETTY, PINGFEST 2026, subtema Lingkungan).

Aplikasi ini mengikuti alur kerja SeaTracker Hybrid:

1. **Lapor**: warga dan nelayan mengirim foto, lokasi, waktu, dan jenis sampah laut.
2. **Analisis**: AI mengklasifikasi jenis sampah pada foto, lalu petugas memeriksa laporan.
3. **Pemetaan**: laporan digabung per lokasi menjadi peta hotspot.
4. **Prioritas**: hotspot diberi skor dan diurutkan menjadi zona prioritas.
5. **Verifikasi**: tim atau relawan mengecek zona prioritas; hasilnya kembali ke sistem sebagai feedback.

Ditambah halaman **Mikroplastik** (hotspot plastik sebagai petunjuk lokasi sampling), **Data IKLH** (hasil klaster dan analisis spasial dari infografis), dan **Tentang**.

Aplikasi tidak memakai data cuaca atau laut simulasi. Semua angka analisis nasional dan Maluku berasal dari berkas analisis tim.

---

## Cara menjalankan di komputer sendiri

```
pip install -r requirements.txt
streamlit run app.py
```

Aplikasi terbuka di browser pada alamat `http://localhost:8501`.

Di Windows dengan Application Control atau Smart App Control aktif, `streamlit.exe` dan DLL `pyarrow` bisa diblokir. Karena itu:

- Jalankan dengan `python -m streamlit run app.py`, bukan `streamlit run app.py`.
- Jika `pyarrow` tidak bisa dimuat, aplikasi otomatis memakai peta HTML biasa dan tabel HTML. Semua halaman tetap berjalan; bedanya, lokasi di halaman Lapor dipilih dari daftar lokasi atau diisi manual, bukan dengan klik peta.
- `jalankan.bat` dan tombol Run di VS Code (`.vscode/launch.json`) sudah memakai cara ini.

---

## Struktur folder

```
OceanPatrol/
├── app.py                  File utama. Mengatur halaman, navbar, dan memanggil halaman yang dipilih.
├── requirements.txt        Daftar library yang dipasang Streamlit Cloud.
├── .streamlit/config.toml  Warna tema dasar Streamlit (tidak diubah).
├── assets/
│   ├── style.css           Semua CSS tampilan.
│   └── templates/          Kerangka HTML setiap kartu dan blok tampilan (file .html).
├── core/                   Logika dan perhitungan (tanpa tampilan).
│   ├── config.py           Konstanta: warna, daftar menu, kategori sampah.
│   ├── data.py             Membaca CSV dan menyimpan data selama sesi.
│   ├── geo.py              Fungsi geografi: jarak, titik di dalam teluk, mata angin.
│   ├── hotspot.py          Menghitung hotspot dari laporan.
│   ├── priority.py         Skor dan tingkat prioritas zona.
│   ├── classifier.py       Simulasi analisis foto.
│   └── pipeline.py         Menyambungkan semua langkah di atas.
├── components/             Potongan tampilan yang dipakai berulang.
│   ├── ui.py               Kartu, judul halaman, kotak info, legenda, gaya grafik.
│   └── maps.py             Pembuat peta Folium dan lapisannya.
├── views/                  Satu file untuk satu halaman.
│   ├── dashboard.py
│   ├── lapor.py
│   ├── analisis_ai.py
│   ├── pemetaan.py
│   ├── prediksi.py         Tahap berikutnya (prediksi pergerakan): cara kerja, kebutuhan data, calon mitra. Tanpa angka prediksi.
│   ├── prioritas.py
│   ├── verifikasi.py
│   ├── mikroplastik.py
│   ├── data_iklh.py
│   └── tentang.py
└── data/                   Semua data CSV dan GeoJSON.
```

Folder halaman sengaja dinamai `views`, bukan `pages`. Streamlit otomatis membuat menu samping untuk folder bernama `pages`, dan itu akan bentrok dengan navbar buatan sendiri.

---

## Penjelasan kode

### app.py

File yang dijalankan Streamlit Cloud. Isinya hanya tiga hal:

1. `st.set_page_config` dan `ui.load_css()` untuk mengatur judul tab dan memuat `assets/style.css`.
2. Navbar tetap di atas. Setiap menu adalah `st.button`. Saat diklik, nama halaman disimpan ke `st.session_state["page"]`.
3. Kamus `HALAMAN` menghubungkan nama menu dengan fungsi `render()` di folder `views`, lalu halaman yang dipilih dipanggil.

Tombol **LAPORAN BARU** di navbar mengembalikan data ke kondisi awal, menambah tiga laporan baru di Pasar Mardika, lalu membuka halaman Prioritas. Zona yang menerima laporan baru diberi tanda sehingga terlihat bagaimana laporan warga langsung mengubah urutan prioritas. Tombol ini dipakai saat presentasi.

### assets/style.css

Semua CSS yang dulu ada di dalam `app.py` dipindah ke sini. Warna dasar tetap sama:

| Warna | Kode | Dipakai untuk |
|---|---|---|
| Biru tua | `#05162a` sampai `#0a2e5c` | Latar belakang dan navbar |
| Biru panel | `#112240` | Panel dan kartu |
| Biru cerah | `#00d2ff` | Aksen utama, judul panel, tombol |
| Hijau mint | `#64ffda` | Kotak info, lokasi sensitif |
| Merah | `#ff4b4b` | Prioritas tinggi |
| Oranye | `#f5a623` | Prioritas sedang, menunggu verifikasi |

Kartu besar dashboard (hijau, ungu, merah muda) memakai gradasi yang sama dengan versi sebelumnya.

### core/data.py

- `baca_csv(nama)` membaca file dari folder `data` dan menyimpannya di cache.
- `init_state()` menyalin data laporan dan verifikasi ke `st.session_state` saat sesi dimulai.
- `tambah_laporan()`, `tambah_verifikasi()`, `ubah_status_laporan()` menambah dan mengubah data selama sesi.
- `reset_demo()` mengembalikan data ke isi CSV awal.

Data baru hanya tersimpan selama sesi berjalan, tidak ditulis ke file. Ini disengaja agar data demo di Streamlit Cloud tidak rusak saat banyak orang mencoba. Data bisa diunduh sebagai CSV di halaman Tindak.

### core/hotspot.py

`hitung_hotspot()` membagi peta menjadi sel grid sekitar 900 m. Setiap laporan diberi bobot sesuai perkiraan jumlah (Sedikit 1, Sedang 3, Banyak 6). Total bobot dalam satu sel menjadi skor kepadatan. Untuk setiap sel juga dihitung jumlah laporan, laporan 7 hari terakhir, porsi plastik, kategori dominan, dan daftar ID laporan. Sel diberi tingkat:

- Tinggi: di atas 65 persen skor tertinggi
- Sedang: 35 sampai 65 persen
- Rendah: di bawah 35 persen

Laporan berstatus Ditolak tidak dihitung.

### core/priority.py

`zona_prioritas()` mengubah setiap hotspot menjadi zona dengan skor:

```
skor = 0,45 x kepadatan laporan (dibanding hotspot tertinggi)
     + 0,20 x laporan 7 hari terakhir (dibanding zona teraktif)
     + 0,15 x porsi sampah plastik dan styrofoam
     + 0,20 x kedekatan dengan lokasi sensitif (keramba, mangrove, permukiman, pasar)
```

Tingkat prioritas: Tinggi bila skor di atas 0,65, Sedang di atas 0,40, selain itu Rendah. Setiap tingkat punya rekomendasi aksi. Bobot bisa diubah di kamus `BOBOT`.

### core/classifier.py

Simulasi analisis foto. Fungsi `analisis_foto()` membaca warna foto dengan Pillow lalu menghasilkan kategori sampah dan tingkat keyakinan. Foto yang sama selalu memberi hasil yang sama. Untuk versi produksi, isi fungsi ini cukup diganti dengan model deteksi objek (misalnya YOLO) tanpa mengubah halaman lain.

### core/pipeline.py

Menyambungkan semua modul. Halaman cukup memanggil `pipeline.hotspot()` dan `pipeline.zona()`. Hasilnya disimpan di cache, jadi berpindah halaman tidak menghitung ulang selama data laporan sama.

### components/ui.py

Fungsi kecil untuk tampilan, misalnya `dash_card()`, `fact()`, `info_box()`, `flow()`, `legend()`, `bar()`, dan `style_fig()` untuk menyamakan gaya grafik Plotly. Kerangka HTML tidak ditulis di Python, tetapi di `assets/templates/*.html` dengan penanda `{{nama}}`. `tpl()` membaca template dan mengisi nilainya, `tampil()` langsung menampilkannya. `md()` membuang baris kosong dari HTML agar blok HTML tidak terpotong oleh Markdown. `table()` memakai `st.dataframe` jika `pyarrow` tersedia, dan tabel HTML jika tidak.

### components/maps.py

`base_map()` membuat peta gelap Carto dengan peta cadangan Esri. `show()` menampilkan peta dengan `streamlit-folium` jika `pyarrow` tersedia, dan dengan iframe HTML biasa jika tidak. Fungsi `add_...()` menambah lapisan: heatmap, titik laporan, data survei literatur, lokasi sensitif, peringkat hotspot, zona prioritas, dan rencana sampling mikroplastik. `finish()` menambah pengatur lapisan di pojok peta.

### views

Setiap file punya satu fungsi `render()`.

| Halaman | Isi |
|---|---|
| Dashboard | Tiga kartu ringkasan, alur enam langkah, peta gabungan, konteks area pertama (IKLH Maluku, SIPSN, survei Poka), fakta Teluk Ambon. |
| Lapor | Formulir laporan dengan unggah foto, pilih lokasi dengan klik peta, hasil analisis foto. |
| Analisis | Ringkasan hasil AI, kecocokan AI dengan pelapor, antrean laporan dengan tombol Terima dan Tolak. |
| Pemetaan | Filter laporan, heatmap, peringkat hotspot, komposisi sampah, data survei literatur, riwayat laporan per minggu. |
| Prediksi | Tahap berikutnya dari alur: cara kerja, kebutuhan data, calon mitra, dan keluaran. Tidak menampilkan angka prediksi karena data arus dan angin resmi belum ada. |
| Prioritas | Zona prioritas dengan skor, rekomendasi, objek sensitif terdekat, dan rincian alasan skor. |
| Verifikasi | Formulir cek lapangan per zona, riwayat verifikasi, status laporan, unduh CSV. |
| Mikroplastik | Alur makro ke mikro, fakta mikroplastik Teluk Ambon, rencana titik sampling. |
| Data IKLH | Peta klaster, IKLH 34 provinsi, penjelajah provinsi, LISA, perbandingan OLS/SAR/SEM, koefisien SEM, sorotan Maluku dan Kota Ambon. |
| Tentang | Deskripsi solusi, fitur unggulan, stakeholder, manfaat, SWOT, kelebihan, kekurangan, keterbatasan, sumber data. |

---

## Data

| File | Isi | Status |
|---|---|---|
| `reports.csv` | 30 laporan warga beserta hasil AI | Data demo |
| `survei_literatur.csv` | Kepadatan sampah pesisir Poka, Tawiri, rata-rata, Tanjung Martafons, BTN Passo Indah | Literatur dan poster |
| `klaster_iklh.csv` | Rata-rata IKLH, jumlah provinsi, median kepadatan tiap klaster | Hasil analisis tim |
| `iklh_provinsi.csv` | IKLH, kepadatan, timbulan, plastik, klaster, dan LISA 34 provinsi | Hasil analisis tim (notebook) |
| `model_spasial.csv` | Perbandingan OLS, SAR, SEM (R2, AIC, RMSE) | Hasil analisis tim (notebook) |
| `koefisien_sem.csv` | Koefisien dan p-value Spatial Error Model | Hasil analisis tim (notebook) |
| `timbulan_maluku_sipsn2024.csv` | Timbulan sampah dan porsi plastik kabupaten/kota Maluku | SIPSN KLHK 2024 |
| `lokasi.csv` | Nama tempat di sekitar Teluk Ambon | Koordinat perkiraan |
| `lokasi_sensitif.csv` | Keramba, mangrove, wisata, permukiman, pasar | Koordinat perkiraan |
| `teluk_ambon_perairan.geojson` | Batas perairan teluk untuk peta | Digambar manual |
| `verification.csv` | Kepala kolom verifikasi | Kosong |

Data IKLH diambil dari `data_final_34_provinsi.csv` dan hasil notebook `Analisis_IKLH_Indonesia_34_Provinsi.ipynb` di folder Drive tim. Peta klaster (`assets/peta_klaster.png`) berasal dari notebook yang sama dengan warna disesuaikan tema aplikasi. Maluku Utara tidak tersedia dalam dataset.

### Kolom reports.csv

`report_id, timestamp, latitude, longitude, lokasi, jenis, kategori, ai_kategori, estimasi_jumlah, pelapor, confidence, status, foto`

- `jenis`: Terapung atau Terdampar
- `kategori`: pilihan pelapor; `ai_kategori`: hasil AI. Nilainya Plastik kemasan, Botol plastik, Kantong plastik, Styrofoam, Alat tangkap, Sampah campuran
- `estimasi_jumlah`: Sedikit, Sedang, Banyak
- `status`: Terverifikasi, Menunggu verifikasi, Ditolak

---

## Sumber

- World Bank, Plastic Waste Discharges from Rivers and Coastlines in Indonesia: sekitar 83 persen kebocoran plastik darat ke laut dibawa sungai.
- Jurnal Omni-Akuatika (sampel 2017, terbit 2021): 2.359 item sampah pesisir, rata-rata 18,87 item/m2, Poka 68,74 item/m2, Teluk Ambon Dalam sekitar 3 kali Teluk Ambon Luar, seluruh stasiun Very Dirty.
- Publikasi mikroplastik Teluk Ambon (2022): konsentrasi permukaan Teluk Ambon Dalam sekitar 7,5 kali Teluk Ambon Luar; serat dan film pada Caranx sexfasciatus budidaya.
- Analisis tim IRIS PRETTY: IKLH 34 provinsi, K-Means, Moran's I, LISA, OLS, SAR, SEM.
- SIPSN KLHK 2024: timbulan dan komposisi sampah kabupaten/kota. BPS 2024: kepadatan penduduk provinsi.
- Poster OceanPatrol: data ekonomi, Tanjung Martafons, BTN Passo Indah, tekanan populasi pesisir.

---

## Batasan prototipe

- Laporan warga (reports.csv) adalah data peragaan; tidak ada data cuaca atau laut dalam aplikasi. Tampilan aplikasi tidak memberi label khusus, sehingga keterangannya hanya ada di README ini dan di halaman Tentang (tab Evaluasi dan tab Sumber dan status data). Sampaikan saat presentasi bila ditanya.
- Analisis foto masih simulasi. Kamera tidak mendeteksi mikroplastik.
- Zona prioritas adalah rekomendasi berdasarkan laporan, bukan kepastian; tetap perlu verifikasi lapangan.
- Batas teluk dan koordinat lokasi adalah perkiraan. Versi produksi memakai garis pantai BIG atau OpenStreetMap.
- Data baru hanya tersimpan selama sesi. Penyimpanan permanen membutuhkan basis data.


## Memisahkan tampilan dari logika

Tampilan ada di dua tempat: `assets/templates/*.html` untuk struktur HTML dan `assets/style.css` untuk gaya. Untuk mengubah isi atau tata letak sebuah kartu, edit file `.html` yang namanya sama dengan nama template yang dipanggil di Python, misalnya `zona_card.html` dipanggil lewat `ui.tampil("zona_card", ...)`. Penanda `{{warna}}` di template diisi dari argumen `warna=...` pada pemanggilan. Grafik Plotly, peta Folium, formulir, dan tombol tetap dibuat dari Python karena merupakan komponen interaktif Streamlit.

## Tampilan peta, tabel, footer, dan animasi

- **Peta**: hotspot dan zona prioritas digambar sebagai lingkaran besar berwarna dengan garis tepi putih. Ukuran lingkaran mengikuti indeks kepadatan atau skor, warnanya mengikuti tingkat (merah tinggi, kuning sedang, biru rendah). Legenda ada di dalam peta lewat `maps.add_legend()`, gayanya ditulis di `assets/templates/map_legend.html` karena peta tampil di dalam iframe sendiri yang tidak membaca `style.css`.
- **Tabel hotspot**: halaman Pemetaan memakai `tabel_hotspot.html` dan `tabel_hotspot_baris.html`. Ada kolom pencarian dan pilihan urutan. Header tidak bisa diklik untuk mengurutkan karena Streamlit tidak menjalankan JavaScript buatan sendiri.
- **Footer**: `assets/templates/footer.html`, dipanggil di akhir `app.py` sehingga muncul di semua halaman. Isi (sumber data, alur kerja) diubah langsung di file itu.
- **Animasi**: bagian "Animasi masuk dan keluar" di `assets/style.css`. Semua peramban memberi animasi masuk (naik dan memudar) saat halaman dibuka. Chrome dan Edge terbaru juga memberi animasi saat gulir: kartu muncul ketika masuk layar dan memudar pelan ketika keluar di sisi atas. Firefox dan Safari lama hanya menampilkan animasi masuk. Animasi dimatikan otomatis bagi pengguna yang mengaktifkan "kurangi gerakan" di sistemnya.

## Cakupan Indonesia, peta, dan lokasi otomatis

- **Cakupan**: Teluk Ambon adalah wilayah awal. Alurnya tidak terikat satu lokasi: laporan dari wilayah lain tetap diterima dan dipetakan dengan koordinatnya (`geo.nama_lokasi()` memberi nama berbentuk koordinat bila lokasi acuan terdekat lebih jauh dari 25 km). Untuk wilayah baru, tambahkan baris di `data/lokasi.csv` dan `data/lokasi_sensitif.csv`, batas perairan, dan data kondisi perairan setempat.
- **Pilihan tampilan peta**: Dashboard dan Pemetaan punya pilihan Teluk Ambon, Indonesia, dan Dunia (`maps.VIEWS`). Tampilan Indonesia dan Dunia menggambar batas provinsi yang diwarnai menurut klaster IKLH (`maps.add_provinsi_poligon`), Maluku diberi garis putih tebal, dan laporan OceanPatrol sebagai gelembung yang terurai saat peta didekati (`maps.add_laporan_klaster`). Daratan dunia digambar sebagai vektor (`maps.add_dunia`), jadi bentuk Indonesia tetap tampil walau peta dasar online gagal dimuat.
- **Lokasi otomatis di Lapor**: halaman Lapor meminta lokasi perangkat lewat `streamlit-js-eval` (`get_geolocation`). Browser menampilkan izin lokasi sekali. Setelah diizinkan, koordinat formulir dan titik peta terisi sendiri. Pelapor tetap bisa mengeklik peta atau memilih lokasi dari daftar. Fitur ini butuh HTTPS (Streamlit Cloud sudah HTTPS) atau `localhost`, dan butuh `pyarrow`.
- **Menu aktif di navbar**: halaman yang sedang dibuka diberi kotak menyala. Aturannya dibuat di `assets/templates/nav_aktif.html`.
- **Ukuran teks**: diatur satu tempat, `html { font-size: ... }` di bagian atas `assets/style.css`. Ubah angka itu untuk memperbesar atau memperkecil seluruh tampilan.

## Peta dasar dan data batas wilayah

- **Peta dasar**: Esri World Dark Gray (tanpa kunci API). Carto tidak dipakai lagi karena sekarang meminta kunci API dan menampilkan tulisan "API KEY REQUIRED" di setiap tile. Peta jalan OpenStreetMap tersedia sebagai cadangan lewat pengatur lapisan di pojok kanan atas peta.
- `data/indonesia_provinsi.geojson`: batas 34 provinsi, bersumber dari repositori `ans-4175/peta-indonesia-geojson` (Peta Dasar BAKOSURTANAL dan batas provinsi Dukcapil 2019), disederhanakan agar ringan. Karena batas ini sebelum pemekaran Papua 2022, Papua Selatan tidak punya poligon sendiri dan ikut dalam poligon Papua. Maluku Utara berwarna abu-abu karena tidak ada dalam dataset IKLH.
- `data/dunia_negara.geojson`: batas negara dari Natural Earth 110m (domain publik) lewat paket `world-atlas`, disederhanakan, tanpa Antartika.
