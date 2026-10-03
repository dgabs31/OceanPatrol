"""Simulasi analisis foto sampah laut.

Prototipe ini belum memakai model AI terlatih. Fungsi di bawah mengekstrak ciri
warna sederhana dari foto lalu menghasilkan skor kategori yang konsisten untuk
foto yang sama. Untuk versi produksi, fungsi analisis_foto bisa diganti dengan
model deteksi objek (misalnya YOLO) yang dilatih dengan dataset sampah laut,
tanpa mengubah halaman lain.
"""

import hashlib
import io
import random

from PIL import Image, ImageStat

from core.config import KATEGORI_SAMPAH


def _ciri_warna(img):
    """Kecerahan, saturasi, dan dominasi kanal warna."""
    kecil = img.convert("RGB").resize((96, 96))
    r, g, b = ImageStat.Stat(kecil).mean
    hsv = kecil.convert("HSV")
    _, s, v = ImageStat.Stat(hsv).mean
    return {"r": r, "g": g, "b": b, "saturasi": s / 255, "kecerahan": v / 255}


def analisis_foto(file_bytes):
    """Mengembalikan label, keyakinan, dan tiga kandidat kategori."""
    img = Image.open(io.BytesIO(file_bytes))
    ciri = _ciri_warna(img)

    seed = int(hashlib.md5(file_bytes).hexdigest()[:8], 16)
    rng = random.Random(seed)
    skor = {k: rng.uniform(0.2, 1.0) for k in KATEGORI_SAMPAH}

    # Aturan sederhana berbasis warna agar hasil terasa masuk akal
    if ciri["kecerahan"] > 0.7 and ciri["saturasi"] < 0.2:
        skor["Styrofoam"] += 0.9
    if ciri["saturasi"] > 0.45:
        skor["Plastik kemasan"] += 0.7
    if ciri["b"] > ciri["r"] and ciri["b"] > ciri["g"]:
        skor["Botol plastik"] += 0.5
    if ciri["kecerahan"] < 0.35:
        skor["Alat tangkap"] += 0.4
        skor["Sampah campuran"] += 0.4

    total = sum(skor.values())
    urut = sorted(((k, v / total) for k, v in skor.items()), key=lambda x: x[1], reverse=True)
    top3 = urut[:3]
    keyakinan = round(min(0.95, 0.5 + top3[0][1] * 1.5), 2)
    return {
        "label": top3[0][0],
        "keyakinan": keyakinan,
        "kandidat": [(k, round(v, 3)) for k, v in top3],
        "terdeteksi_sampah": True,
        "ciri": {k: round(v, 2) for k, v in ciri.items()},
    }
