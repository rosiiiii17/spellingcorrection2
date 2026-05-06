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
    return re.sub(r'(.)\1+', r'\1', word)

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
# FILTERING
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
# TOP 3 DLD (SAMA SPT SKENARIO 1)
# ======================
def prediksi_top3_dld(kata):

    kandidat = filtering_kamus(kata)

    ranking = []

    for k in kandidat:
        jarak = damerau_levenshtein_distance(kata, k)
        ranking.append((k, jarak))

    ranking.sort(key=lambda x: x[1])

    return [x[0] for x in ranking[:3]]

# ======================
# PERBAIKI 1 KATA (DLD)
# ======================
def perbaiki_kata_dld(kata):

    kandidat = filtering_kamus(kata)

    ranking = []

    for k in kandidat:
        jarak = damerau_levenshtein_distance(kata, k)
        ranking.append((k, jarak))

    ranking.sort(key=lambda x: x[1])

    if ranking and ranking[0][1] <= 2:
        return ranking[0][0]

    return kata

# ======================
# EMPIRIS (SPLIT)
# ======================
def metode_empiris(kata):

    hasil = []

    for i in range(1, len(kata)):
        kiri = kata[:i]
        kanan = kata[i:]

        if kiri in kamus_txt and kanan in kamus_txt:
            hasil.append((kiri, kanan))

    return hasil

# ======================
# MODEL FINAL
# ======================
def prediksi_final(kata):

    kata = kata.lower()

    # ======================
    # DLD
    # ======================
    kandidat = filtering_kamus(kata)

    ranking = []

    for k in kandidat:
        jarak = damerau_levenshtein_distance(kata, k)
        ranking.append((k, jarak))

    ranking.sort(key=lambda x: x[1])

    top3 = [x[0] for x in ranking[:3]] if ranking else []

    # ✅ jika DLD berhasil
    if ranking and ranking[0][1] <= 2:
        return ranking[0][0], "DLD", top3

    # ======================
    # EMPIRIS
    # ======================
    hasil_empiris = metode_empiris(kata)

    if hasil_empiris:

        kiri, kanan = hasil_empiris[0]

        kiri_fix = perbaiki_kata_dld(kiri)
        kanan_fix = perbaiki_kata_dld(kanan)

        return f"{kiri_fix} {kanan_fix}", "EMPIRIS", []

    # ======================
    # FALLBACK
    # ======================
    return kata, "TIDAK DIKOREKSI", top3

# ======================
# UI
# ======================
st.title("Spelling Correction - Skenario 2")
st.write("Metode: DLD + Empiris")

teks = st.text_area("Masukkan kalimat:")

if st.button("Koreksi"):

    hasil_kalimat = []
    detail = []

    for kata in teks.split():

        hasil, metode, top3 = prediksi_final(kata)

        hasil_kalimat.append(hasil)

        if metode != "DLD":
            detail.append((kata, hasil, metode, top3))

    # ======================
    # HASIL (BERSIH)
    # ======================
    st.subheader("Hasil:")
    st.success(" ".join(hasil_kalimat))

    # ======================
    # PERBAIKAN
    # ======================
    st.subheader("Perbaikan Kata:")

    for kata, hasil, metode, top3 in detail:

        if metode == "EMPIRIS":
            st.info(f"{kata} → {hasil} (EMPIRIS)")

        elif metode == "TIDAK DIKOREKSI":
            st.warning(f"{kata} → tidak bisa dikoreksi")

            if top3:
                st.write("Top Kandidat:")
                for i, k in enumerate(top3, 1):
                    st.write(f"{i}. {k}")