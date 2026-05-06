import streamlit as st
import re
import json
import gzip

# ======================
# LOAD TXT (FILTERING)
# ======================
with open("kbbi_dataset.txt", "r", encoding="utf-8") as f:
    kamus_txt = set([
        line.strip().lower()
        for line in f
        if " " not in line.strip()
    ])

# ======================
# LOAD JSON GZIP (PENGECEKAN)
# ======================
@st.cache_data
def load_kamus_json():
    with gzip.open("kbbi.json.gz", "rt", encoding="utf-8") as f:
        data = json.load(f)
    return set([item["kata"] for item in data if "kata" in item])

try:
    kamus_json = load_kamus_json()
except:
    st.error("Gagal load kamus JSON")
    st.stop()

# ======================
# NORMALISASI
# ======================
def normalize_word(word):
    return re.sub(r'(.)\1+', r'\1', word)

# ======================
# CEK KAMUS (JSON)
# ======================
def cek_kamus_lengkap(kata):
    if kata in kamus_json:
        return "BENAR"
    if not re.match(r'^[a-z]+$', kata):
        return "UNKNOWN"
    if len(kata) <= 2:
        return "UNKNOWN"
    return "SALAH"

# ======================
# DLD
# ======================
def damerau_levenshtein_distance(s1, s2):
    d = {}
    for i in range(-1, len(s1)+1):
        d[(i, -1)] = i+1
    for j in range(-1, len(s2)+1):
        d[(-1, j)] = j+1

    for i in range(len(s1)):
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i-1, j)] + 1,
                d[(i, j-1)] + 1,
                d[(i-1, j-1)] + cost
            )
            if i and j and s1[i] == s2[j-1] and s1[i-1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i-2, j-2)] + cost)

    return d[len(s1)-1, len(s2)-1]

# ======================
# FILTERING (TXT)
# ======================
def filtering_kamus(kata):

    kata = normalize_word(kata)
    hasil = []

    for k in kamus_txt:

        if abs(len(k) - len(kata)) > 2:
            continue

        if kata[0] != k[0]:
            continue

        pola = ".*".join(list(kata))
        if not re.search(pola, k):
            continue

        hasil.append(k)

    return hasil

# ======================
# EMPIRIS (SUDAH DIPERKETAT)
# ======================
def metode_empiris(kata):

    suffix_valid = ["nya", "lah", "kah", "pun", "ku", "mu"]

    for i in range(3, len(kata)-2):

        kiri = kata[:i]
        kanan = kata[i:]

        # filter panjang minimal
        if len(kiri) < 3 or len(kanan) < 3:
            continue

        if kiri in kamus_txt:
            if kanan in kamus_txt or kanan in suffix_valid:
                return kiri, kanan

    return None

# ======================
# MODEL SKENARIO 2 (FIX TOTAL)
# ======================
def proses_kata(kata):

    kata_asli = kata
    kata = kata.lower().strip(",.!?")
    kata = normalize_word(kata)

    status = cek_kamus_lengkap(kata)

    # 1. BENAR
    if status == "BENAR":
        return kata, "BENAR", []

    # ======================
    # 2. DLD (PRIORITAS)
    # ======================
    kandidat = filtering_kamus(kata)

    ranking = []
    for k in kandidat:
        jarak = damerau_levenshtein_distance(kata, k)

        skor = jarak
        skor += abs(len(kata) - len(k)) * 0.5

        if kata[:2] == k[:2]:
            skor -= 0.5

        if kata in k or k in kata:
            skor -= 0.5

        ranking.append((k, skor))

    ranking.sort(key=lambda x: x[1])

    if ranking:
        top3 = ranking[:3]
        kandidat_terbaik, skor = ranking[0]
        return kandidat_terbaik, "DLD", top3

    # ======================
    # 3. EMPIRIS
    # ======================
    split = metode_empiris(kata)
    if split:
        kiri, kanan = split

        kiri_fix, _, _ = proses_kata(kiri)
        kanan_fix, _, _ = proses_kata(kanan)

        return kiri_fix + " " + kanan_fix, "EMPIRIS", []

    # ======================
    # 4. GAGAL
    # ======================
    return kata, "TIDAK DIKOREKSI", []

# ======================
# UI STREAMLIT
# ======================
st.title("Spelling Correction - Skenario 2")
st.write("Metode: DLD + Empiris (Improved)")

teks = st.text_area("Masukkan kalimat:")

if st.button("Koreksi"):

    hasil_kalimat = []
    detail = []

    for kata in teks.split():

        hasil, metode, top3 = proses_kata(kata)

        if metode in ["DLD", "EMPIRIS"] and kata.lower() != hasil:
            hasil_kalimat.append(f"[{kata} → {hasil}]")
        else:
            hasil_kalimat.append(hasil)

        if metode != "BENAR":
            detail.append((kata, hasil, metode, top3))

    st.subheader("Hasil:")
    st.success(" ".join(hasil_kalimat))

    for kata, hasil, metode, top3 in detail:

        if metode == "TIDAK DIKOREKSI":
            st.warning(f"{kata} → tidak bisa dikoreksi")

        elif metode == "EMPIRIS":
            st.info(f"{kata} → {hasil} (EMPIRIS)")

        else:
            st.error(f"{kata} → {hasil} ({metode})")

        if top3:
            st.write("Top Kandidat:")
            for i, (k, j) in enumerate(top3, 1):
                st.write(f"{i}. {k} (skor={round(j,2)})")