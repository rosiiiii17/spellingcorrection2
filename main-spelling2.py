import streamlit as st

# ======================
# LOAD KAMUS
# ======================
with open("kbbi_dataset.txt", "r", encoding="utf-8") as f:
    kamus_txt = set([line.strip() for line in f])


# ======================
# DLD
# ======================
def damerau_levenshtein_distance(s1, s2):
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)

    for i in range(-1, lenstr1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, lenstr2 + 1):
        d[(-1, j)] = j + 1

    for i in range(lenstr1):
        for j in range(lenstr2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,
                d[(i, j - 1)] + 1,
                d[(i - 1, j - 1)] + cost,
            )
            if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)

    return d[lenstr1 - 1, lenstr2 - 1]


# ======================
# FILTER KAMUS
# ======================
def filtering_kamus(kata):
    return [k for k in kamus_txt if abs(len(k) - len(kata)) <= 2]


# ======================
# PERBAIKI DENGAN DLD
# ======================
def perbaiki_dld(kata):

    if kata in kamus_txt:
        return kata, "BENAR"

    kandidat = filtering_kamus(kata)

    ranking = []
    for k in kandidat:
        jarak = damerau_levenshtein_distance(kata, k)
        ranking.append((k, jarak))

    ranking.sort(key=lambda x: x[1])

    if ranking and ranking[0][1] <= 2:
        return ranking[0][0], "DLD"

    return kata, "TIDAK"


# ======================
# EMPIRIS (SPLIT)
# ======================
def metode_empiris(kata):

    for i in range(3, len(kata)-2):

        kiri = kata[:i]
        kanan = kata[i:]

        if kiri in kamus_txt and kanan in kamus_txt:
            return [kiri, kanan]

    return None


# ======================
# PREDIKSI FINAL
# ======================
def prediksi_skenario2(kata):

    kata = kata.lower().strip(",.!?")

    # 1. kalau benar
    if kata in kamus_txt:
        return kata, "BENAR"

    # 2. coba DLD dulu
    hasil_dld, metode = perbaiki_dld(kata)

    if metode == "DLD":
        return hasil_dld, "DLD"

    # 3. kalau gagal → EMPIRIS
    split = metode_empiris(kata)

    if split:
        hasil = []

        for k in split:
            if k in kamus_txt:
                hasil.append(k)
            else:
                hasil.append(perbaiki_dld(k)[0])

        return " ".join(hasil), "EMPIRIS"

    return kata, "TIDAK DIKOREKSI"


# ======================
# UI
# ======================
st.set_page_config(page_title="Skenario 2 - DLD + Empiris")

st.title("🧠 Spelling Correction - Skenario 2")
st.write("Metode: DLD + Empiris (Split Kata)")

teks = st.text_area("Masukkan kalimat:")

if st.button("Koreksi"):

    hasil_kalimat = []
    detail = []

    for kata in teks.split():

        hasil, metode = prediksi_skenario2(kata)

        hasil_kalimat.append(hasil)

        if hasil != kata:
            detail.append((kata, hasil, metode))

    st.subheader("✅ Hasil Perbaikan:")
    st.success(" ".join(hasil_kalimat))

    if detail:
        st.subheader("🔍 Detail:")
        for d in detail:
            st.write(f"❌ {d[0]} → ✅ {d[1]} ({d[2]})")