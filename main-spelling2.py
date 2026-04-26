import streamlit as st

# ======================
# LOAD KAMUS
# ======================
with open("kbbi_dataset.txt", "r", encoding="utf-8") as f:
    kamus_txt = set(line.strip().lower() for line in f)


# ======================
# DLD FUNCTION
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

    return d[(len(s1)-1, len(s2)-1)]


# ======================
# DLD + TOP 3
# ======================
def perbaiki_dld(kata):

    if kata in kamus_txt:
        return kata, 0, []

    kandidat = [k for k in kamus_txt if abs(len(k) - len(kata)) <= 2]

    ranking = []
    for k in kandidat:
        jarak = damerau_levenshtein_distance(kata, k)
        ranking.append((k, jarak))

    ranking.sort(key=lambda x: x[1])

    if ranking:
        top3 = ranking[:3]
        kandidat_terbaik, jarak = ranking[0]
        return kandidat_terbaik, jarak, top3

    return kata, 999, []


# ======================
# EMPIRIS
# ======================
def metode_empiris(kata):

    for i in range(2, len(kata)-1):

        kiri = kata[:i]
        kanan = kata[i:]

        if kiri in kamus_txt and kanan in kamus_txt:
            return kiri, kanan

    return None


# ======================
# MODEL SKENARIO 2
# ======================
def model_skenario2(kata):

    kata = kata.lower().strip(",.!?")

    # 1. BENAR
    if kata in kamus_txt:
        return kata, "BENAR", []

    # 2. DLD
    hasil_dld, jarak, top3 = perbaiki_dld(kata)

    if jarak <= 2:
        return hasil_dld, "DLD", top3

    # 3. EMPIRIS
    split = metode_empiris(kata)

    if split:
        kiri, kanan = split

        kiri_fix, _, _ = perbaiki_dld(kiri)
        kanan_fix, _, _ = perbaiki_dld(kanan)

        return kiri_fix + " " + kanan_fix, "EMPIRIS", []

    # 4. GAGAL
    return kata, "TIDAK DIKOREKSI", top3


# ======================
# UI
# ======================
st.title("🧠 Spelling Correction - Skenario 2")
st.write("Metode: DLD + Empiris + Top 3 Kandidat")

teks = st.text_area("Masukkan kalimat:")

if st.button("Koreksi"):

    hasil_kalimat = []
    detail = []

    for kata in teks.split():

        hasil, metode, top3 = model_skenario2(kata)

        hasil_kalimat.append(hasil)

        if metode != "BENAR":
            detail.append((kata, hasil, metode, top3))

    st.subheader("Hasil:")
    st.success(" ".join(hasil_kalimat))

    st.subheader("Detail:")

    for kata, hasil, metode, top3 in detail:

        if metode == "TIDAK DIKOREKSI":
            st.write(f"⚠️ {kata} → tidak bisa dikoreksi")

        elif metode == "EMPIRIS":
            st.write(f"🔧 {kata} → {hasil} (EMPIRIS)")

        else:
            st.write(f"❌ {kata} → {hasil} ({metode})")

        # 🔥 tampilkan TOP 3 dari DLD
        if top3:
            st.write("   🔎 Top Kandidat:")
            for i, (k, j) in enumerate(top3, start=1):
                st.write(f"   {i}. {k} (jarak={j})")