import streamlit as st
import re
import json
import gzip

# ======================
# LOAD DATA
# ======================
with open("kbbi_dataset.txt", "r", encoding="utf-8") as f:
    kamus_txt = set([
        line.strip().lower()
        for line in f
        if " " not in line.strip()
    ])

@st.cache_data
def load_kamus_json():
    with gzip.open("kbbi.json.gz", "rt", encoding="utf-8") as f:
        data = json.load(f)
    return set([item["kata"] for item in data if "kata" in item])

kamus_json = load_kamus_json()

# ======================
# NORMALISASI
# ======================
def normalize_word(word):
    return re.sub(r'(.)\1+', r'\1', word.lower())

# ======================
# CEK KAMUS
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
# FILTERING KAMUS
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
# DLD + TOP 3
# ======================
def dld_koreksi(kata):

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

    top3 = ranking[:3]

    if ranking and ranking[0][1] <= 2.5:
        return ranking[0][0], top3
    else:
        return None, top3

# ======================
# EMPIRIS (FIXED)
# ======================
def metode_empiris(kata):

    kandidat_split = []

    for i in range(3, len(kata)-2):

        kiri = kata[:i]
        kanan = kata[i:]

        if len(kiri) < 3 or len(kanan) < 3:
            continue

        skor = 0

        if kanan in kamus_txt:
            skor += 2

        if kiri in kamus_txt:
            skor += 2

        if 3 <= len(kiri) <= 7:
            skor += 1

        if 3 <= len(kanan) <= 7:
            skor += 1

        kandidat_split.append((kiri, kanan, skor))

    if kandidat_split:
        kandidat_split.sort(key=lambda x: x[2], reverse=True)
        return kandidat_split[0][0], kandidat_split[0][1]

    return None

# ======================
# PROSES KATA FINAL
# ======================
def proses_kata(kata):

    kata = normalize_word(kata)

    # ======================
    # 1. CEK BENAR
    # ======================
    if kata in kamus_json:
        return kata, "BENAR", []

    # ======================
    # 2. DLD
    # ======================
    hasil_dld, top3 = dld_koreksi(kata)

    if hasil_dld:
        return hasil_dld, "DLD", top3

    # ======================
    # 3. EMPIRIS
    # ======================
    split = metode_empiris(kata)

    if split:
        kiri, kanan = split

        kiri_fix, _, top3_kiri = proses_kata(kiri)
        kanan_fix, _, top3_kanan = proses_kata(kanan)

        hasil = kiri_fix + " " + kanan_fix

        # ambil top3 dari bagian yang diperbaiki
        if kiri_fix != kiri:
            return hasil, "EMPIRIS", top3_kiri
        elif kanan_fix != kanan:
            return hasil, "EMPIRIS", top3_kanan
        else:
            return hasil, "EMPIRIS", []

    # ======================
    # 4. GAGAL
    # ======================
    return kata, "TIDAK DIKOREKSI", top3

# ======================
# STREAMLIT UI
# ======================
st.title("Spelling Correction - Skenario 2")
st.write("Metode: DLD + Empiris")

teks = st.text_area("Masukkan kalimat:")

if st.button("Koreksi"):

    hasil_kalimat = []
    detail = []

    for kata in teks.split():

        hasil, metode, top3 = proses_kata(kata)

        hasil_kalimat.append(hasil)

        if metode != "BENAR":
            detail.append((kata, hasil, metode, top3))

    # ======================
    # HASIL
    # ======================
    st.subheader("Hasil:")
    st.success(" ".join(hasil_kalimat))

    # ======================
    # DETAIL
    # ======================
    st.subheader("Perbaikan Kata:")

    for kata, hasil, metode, top3 in detail:

        if metode == "TIDAK DIKOREKSI":
            st.warning(f"{kata} → tidak bisa dikoreksi")

        elif metode == "EMPIRIS":
            st.info(f"{kata} → {hasil} (EMPIRIS)")

        else:
            st.error(f"{kata} → {hasil} (DLD)")

        # 🔥 TOP 3 SELALU DARI DLD
        if top3:
            st.write("Top Kandidat:")
            for i, (k, s) in enumerate(top3, 1):
                st.write(f"{i}. {k} (skor={round(s,2)})")