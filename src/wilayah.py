"""Normalisasi nama wilayah agar varian penulisan tidak terpecah.

Contoh yang disatukan:
- ``KODYA BANDUNG`` / ``Kodya Bandung`` -> ``Kota Bandung``
- ``KAB. BOGOR`` / ``Kab Bogor`` -> ``Kabupaten Bogor``
- ``SUMATERA UTARA`` -> ``Sumatera Utara``
- ``Nanggroe Aceh Daruss`` -> ``Aceh``
- ``Bangka-Belitung`` -> ``Kepulauan Bangka Belitung``
"""

from __future__ import annotations

import re

import pandas as pd

SENTINEL = "Tidak diketahui"

PROVINSI_ALIAS = {
    "aceh": "Aceh",
    "daerah istimewa aceh": "Aceh",
    "nanggroe aceh darussalam": "Aceh",
    "nanggroe aceh daruss": "Aceh",
    "nangroe aceh darussalam": "Aceh",
    "nangroe aceh daruss": "Aceh",
    "dki jakarta": "DKI Jakarta",
    "jakarta": "DKI Jakarta",
    "jakarta raya": "DKI Jakarta",
    "daerah istimewa yogyakarta": "DI Yogyakarta",
    "di yogyakarta": "DI Yogyakarta",
    "yogyakarta": "DI Yogyakarta",
    "bangka belitung": "Kepulauan Bangka Belitung",
    "bangka-belitung": "Kepulauan Bangka Belitung",
    "kep bangka belitung": "Kepulauan Bangka Belitung",
    "kep. bangka belitung": "Kepulauan Bangka Belitung",
    "kepulauan bangka belitung": "Kepulauan Bangka Belitung",
    "kep riau": "Kepulauan Riau",
    "kepulauan riau": "Kepulauan Riau",
}

# Alias kota/kabupaten yang tidak cukup diselesaikan oleh aturan prefiks.
# Kunci memakai huruf kecil tanpa tanda baca.
KOTA_ALIAS = {
    # Singkatan nama kota
    "kota p siantar": "Kota Pematang Siantar",
    "kota pematang siantar": "Kota Pematang Siantar",
    "kota pematangsiantar": "Kota Pematang Siantar",
    "kota p sidempuan": "Kota Padang Sidempuan",
    "kota padang sidempuan": "Kota Padang Sidempuan",
    "kota padangsidempuan": "Kota Padang Sidempuan",
    "kota tj balai": "Kota Tanjung Balai",
    "kota tanjung balai": "Kota Tanjung Balai",
    "kota tanjungbalai": "Kota Tanjung Balai",
    "kota pekan baru": "Kota Pekanbaru",
    "kota banjar baru": "Kota Banjarbaru",
    "kota lhok seumawe": "Kota Lhokseumawe",
    "kota palangkaraya": "Kota Palangka Raya",
    "kota palangka raya": "Kota Palangka Raya",
    "kota bau bau": "Kota Baubau",
    "kota baubau": "Kota Baubau",
    "kota pare pare": "Kota Parepare",
    "kota sawah lunto": "Kota Sawahlunto",
    "kota bukit tinggi": "Kota Bukittinggi",
    "kota pangkal pinang": "Kota Pangkalpinang",
    "kota pangkalpinang": "Kota Pangkalpinang",
    "kota l linggau": "Kota Lubuk Linggau",
    "kota lubuk linggau": "Kota Lubuk Linggau",
    "kota kotamobagu": "Kota Kotamobagu",
    # Kabupaten: ejaan/penyingkatan/terpotong
    "kabupaten tapanuli selata": "Kabupaten Tapanuli Selatan",
    "kabupaten tapanuli selatan": "Kabupaten Tapanuli Selatan",
    "kabupaten kotawaringin ba": "Kabupaten Kotawaringin Barat",
    "kabupaten kotawaringin bar": "Kabupaten Kotawaringin Barat",
    "kabupaten kotawaringin barat": "Kabupaten Kotawaringin Barat",
    "kabupaten kotawaringin ti": "Kabupaten Kotawaringin Timur",
    "kabupaten kotawaringin tim": "Kabupaten Kotawaringin Timur",
    "kabupaten kotawaringin timur": "Kabupaten Kotawaringin Timur",
    "kabupaten halmahera sel": "Kabupaten Halmahera Selatan",
    "kabupaten halmahera selata": "Kabupaten Halmahera Selatan",
    "kabupaten hulu sungai sel": "Kabupaten Hulu Sungai Selatan",
    "kabupaten hulu sungai teng": "Kabupaten Hulu Sungai Tengah",
    "kabupaten ogan kom ulu": "Kabupaten Ogan Komering Ulu",
    "kabupaten ogan kom ulu sel": "Kabupaten Ogan Komering Ulu Selatan",
    "kabupaten ogan kom ulu tim": "Kabupaten Ogan Komering Ulu Timur",
    "kabupaten ogan komeringulu sel": "Kabupaten Ogan Komering Ulu Selatan",
    "kabupaten ogan komeringulu tim": "Kabupaten Ogan Komering Ulu Timur",
    "kabupaten padang lawas utr": "Kabupaten Padang Lawas Utara",
    "kabupaten pdg lawas utara": "Kabupaten Padang Lawas Utara",
    "kabupaten kutai kertanega": "Kabupaten Kutai Kartanegara",
    "kabupaten tulangbawangbrt": "Kabupaten Tulang Bawang Barat",
    "kabupaten tulang bawang bar": "Kabupaten Tulang Bawang Barat",
    "kabupaten tulang bawang barat": "Kabupaten Tulang Bawang Barat",
    "kabupaten gn kidul": "Kabupaten Gunung Kidul",
    "kabupaten gunung kidul": "Kabupaten Gunung Kidul",
    "kabupaten gn mas kuala ku": "Kabupaten Gunung Mas",
    "kabupaten mluku tnggra brt": "Kabupaten Maluku Tenggara Barat",
    "kabupaten maluku barat dy": "Kabupaten Maluku Barat Daya",
    "kabupaten pangkajene kep": "Kabupaten Pangkajene dan Kepulauan",
    "kabupaten pangkep": "Kabupaten Pangkajene dan Kepulauan",
    "kabupaten bangkep": "Kabupaten Banggai Kepulauan",
    "kabupaten pasir": "Kabupaten Paser",
    "kabupaten bualemo": "Kabupaten Boalemo",
    "kabupaten bireun": "Kabupaten Bireuen",
    "kabupaten simeuleu": "Kabupaten Simeulue",
    "kabupaten kep tanimbar": "Kabupaten Kepulauan Tanimbar",
    "kabupaten kep sitaro": "Kabupaten Kepulauan Sitaro",
    "kabupaten kep anambas": "Kabupaten Kepulauan Anambas",
    "kabupaten kep mentawai": "Kabupaten Kepulauan Mentawai",
    "kabupaten kep sangihe": "Kabupaten Kepulauan Sangihe",
    "kabupaten pulau talibu": "Kabupaten Pulau Taliabu",
    "kabupaten sawah lunto sjj": "Kabupaten Sijunjung",
    "kabupaten dharmas raya": "Kabupaten Dharmasraya",
    "kabupaten toli toli": "Kabupaten Tolitoli",
    "kabupaten tojo una una": "Kabupaten Tojo Una-Una",
    "kabupaten labuhan bt sel": "Kabupaten Labuhanbatu Selatan",
    "kabupaten labuhan bt utara": "Kabupaten Labuhanbatu Utara",
    "kabupaten lbuhn baru sltn": "Kabupaten Labuhanbatu Selatan",
    "kabupaten lbuhn baru utra": "Kabupaten Labuhanbatu Utara",
    "kabupaten tanjung jab bar": "Kabupaten Tanjung Jabung Barat",
    "kabupaten tanjung jab tim": "Kabupaten Tanjung Jabung Timur",
    "kabupaten tim tgh selatan": "Kabupaten Timor Tengah Selatan",
    "kabupaten tim tgh utara": "Kabupaten Timor Tengah Utara",
    "kabupaten penajam paser ut": "Kabupaten Penajam Paser Utara",
    "kabupaten kuantan s": "Kabupaten Kuantan Singingi",
    "kabupaten bolmong": "Kabupaten Bolaang Mongondow",
    "kabupaten bolmong induk": "Kabupaten Bolaang Mongondow",
    "kabupaten bolmong selatan": "Kabupaten Bolaang Mongondow Selatan",
    "kabupaten bolmong timur": "Kabupaten Bolaang Mongondow Timur",
    "kabupaten bolmong utara": "Kabupaten Bolaang Mongondow Utara",
    "kabupaten minahasa induk": "Kabupaten Minahasa",
    "kabupaten minahasa sel": "Kabupaten Minahasa Selatan",
    "kabupaten parimo": "Kabupaten Parigi Moutong",
    "kabupaten banggai daratan": "Kabupaten Banggai",
    "kabupaten selayar": "Kabupaten Kepulauan Selayar",
    "kabupaten pulau talibu": "Kabupaten Pulau Taliabu",
    # Nama tanpa prefiks yang ejaannya berbeda dari bentuk baku
    "bangka induk": "Kabupaten Bangka",
    "pasir": "Kabupaten Paser",
    "bualemo": "Kabupaten Boalemo",
    "bireun": "Kabupaten Bireuen",
    "simeuleu": "Kabupaten Simeulue",
    "pangkep": "Kabupaten Pangkajene dan Kepulauan",
    "bangkep": "Kabupaten Banggai Kepulauan",
    "selayar": "Kabupaten Kepulauan Selayar",
    # Nama kabupaten/kota yang ditulis tanpa prefiks di sebagian dataset
    "bangka barat": "Kabupaten Bangka Barat",
    "bangka selatan": "Kabupaten Bangka Selatan",
    "bangka tengah": "Kabupaten Bangka Tengah",
    "banyuasin": "Kabupaten Banyuasin",
    "batanghari": "Kabupaten Batanghari",
    "belitung barat": "Kabupaten Belitung Barat",
    "belitung timur": "Kabupaten Belitung Timur",
    "bengkulu selatan": "Kabupaten Bengkulu Selatan",
    "bengkulu tengah": "Kabupaten Bengkulu Tengah",
    "bengkulu utara": "Kabupaten Bengkulu Utara",
    "bungo": "Kabupaten Bungo",
    "buton tengah": "Kabupaten Buton Tengah",
    "humbang hasudutan": "Kabupaten Humbang Hasundutan",
    "jayawijaya": "Kabupaten Jayawijaya",
    "kaur": "Kabupaten Kaur",
    "kepahyang": "Kabupaten Kepahiang",
    "kerinci": "Kabupaten Kerinci",
    "kulon progo": "Kabupaten Kulon Progo",
    "lahat": "Kabupaten Lahat",
    "lanny jaya": "Kabupaten Lanny Jaya",
    "lebong": "Kabupaten Lebong",
    "maluku tenggara": "Kabupaten Maluku Tenggara",
    "mamberamo tengah": "Kabupaten Mamberamo Tengah",
    "merangin": "Kabupaten Merangin",
    "muara enim": "Kabupaten Muara Enim",
    "muara jambi": "Kabupaten Muara Jambi",
    "muko muko": "Kabupaten Muko Muko",
    "musi banyuasin": "Kabupaten Musi Banyuasin",
    "musi rawas": "Kabupaten Musi Rawas",
    "nabire": "Kabupaten Nabire",
    "nduga": "Kabupaten Nduga",
    "ogan ilir": "Kabupaten Ogan Ilir",
    "ogan komering ilir": "Kabupaten Ogan Komering Ilir",
    "ogan komering ulu": "Kabupaten Ogan Komering Ulu",
    "ogan komeringulu sel": "Kabupaten Ogan Komering Ulu Selatan",
    "ogan komeringulu tim": "Kabupaten Ogan Komering Ulu Timur",
    "pasangkayu": "Kabupaten Pasangkayu",
    "pegunungan bintang": "Kabupaten Pegunungan Bintang",
    "prabumulih": "Kota Prabumulih",
    "rejang lebong": "Kabupaten Rejang Lebong",
    "sarolangun": "Kabupaten Sarolangun",
    "seluma": "Kabupaten Seluma",
    "serdang bedagai": "Kabupaten Serdang Bedagai",
    "tanjung jabung barat": "Kabupaten Tanjung Jabung Barat",
    "tanjung jabung timur": "Kabupaten Tanjung Jabung Timur",
    "tebo": "Kabupaten Tebo",
    "tegal kodia": "Kota Tegal",
    "kabupaten sangihe": "Kabupaten Kepulauan Sangihe",
    "kabupaten lima puluh koto": "Kabupaten Lima Puluh Kota",
    "kota mamuju": "Kabupaten Mamuju",
    "kabupaten salatiga": "Kota Salatiga",
    "kabupaten ogan kom ilir": "Kabupaten Ogan Komering Ilir",
    "kabupaten penajam": "Kabupaten Penajam Paser Utara",
    "kabupaten polewali": "Kabupaten Polewali Mandar",
    "kabupaten batu": "Kota Batu",
    "kota tangerang sel": "Kota Tangerang Selatan",
    "kota jakarta selata": "Kota Jakarta Selatan",
    "tolikara": "Kabupaten Tolikara",
    "yahukimo": "Kabupaten Yahukimo",
    "yalimo": "Kabupaten Yalimo",
}

_BERSIH = re.compile(r"\s+")


def _rapikan_teks(nilai) -> str:
    teks = "" if pd.isna(nilai) else str(nilai).strip()
    if not teks:
        return ""
    teks = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", teks)
    teks = teks.replace("_", " ").replace("-", " ")
    teks = re.sub(r"[.,]", " ", teks)
    return _BERSIH.sub(" ", teks).strip()


def _title(teks: str) -> str:
    return " ".join(kata.capitalize() for kata in teks.split())


def _kunci(teks: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", teks.lower()).strip()


def normalisasi_provinsi(nilai) -> str:
    teks = _rapikan_teks(nilai)
    if not teks:
        return SENTINEL
    if teks.lower() == SENTINEL.lower():
        return SENTINEL
    teks = _title(teks)
    return PROVINSI_ALIAS.get(_kunci(teks), teks)


def normalisasi_kota(nilai) -> str:
    teks = _rapikan_teks(nilai)
    if not teks:
        return SENTINEL
    if teks.lower() == SENTINEL.lower():
        return SENTINEL

    low = teks.lower()
    cocok = re.match(r"^(kabupaten|kab)\b\s*", low)
    if cocok:
        hasil = "Kabupaten " + _title(teks[cocok.end() :].strip())
    else:
        cocok = re.match(r"^(kotamadya|kodya|kod|kota administrasi|kota)\b\s*", low)
        if cocok:
            hasil = "Kota " + _title(teks[cocok.end() :].strip())
        else:
            cocok = re.search(r"\s+kota$", low)
            if cocok:
                hasil = "Kota " + _title(teks[: cocok.start()].strip())
            else:
                hasil = _title(teks)

    return KOTA_ALIAS.get(_kunci(hasil), hasil)


def normalisasi_kecamatan(nilai) -> str:
    teks = _rapikan_teks(nilai)
    if not teks:
        return SENTINEL
    if teks.lower() == SENTINEL.lower():
        return SENTINEL
    return _title(teks)


def normalisasi_desa(nilai) -> str:
    teks = _rapikan_teks(nilai)
    if not teks:
        return SENTINEL
    if teks.lower() == SENTINEL.lower():
        return SENTINEL
    return _title(teks)


NORMALISATOR = {
    "provinsi": normalisasi_provinsi,
    "kota": normalisasi_kota,
    "kecamatan": normalisasi_kecamatan,
    "desa": normalisasi_desa,
}


def _rapikan_prefiks_kota(series: pd.Series) -> pd.Series:
    """Lengkapi nama kota/kabupaten yang ditulis tanpa prefiks.

    Contoh: bila dalam satu kolom ada ``Bangka Tengah`` dan
    ``Kabupaten Bangka Tengah``, yang pertama disamakan dengan yang kedua.
    Tidak dilakukan bila nama yang sama punya tipe Kota dan Kabupaten sekaligus.
    """
    nilai = series.copy()
    kandidat: dict[str, set[str]] = {}
    for teks in nilai.dropna().unique():
        if teks.startswith(("Kabupaten ", "Kota ")):
            kunci = _kunci(re.sub(r"^(Kabupaten|Kota)\s+", "", teks))
            kandidat.setdefault(kunci, set()).add(teks)
    peta = {k: next(iter(v)) for k, v in kandidat.items() if len(v) == 1}
    for idx, teks in nilai.items():
        if isinstance(teks, str) and not teks.startswith(("Kabupaten ", "Kota ")):
            kanonik = peta.get(_kunci(teks))
            if kanonik:
                nilai.at[idx] = kanonik
    return nilai


def normalisasi_kolom(
    df: pd.DataFrame,
    kolom: dict[str, str],
) -> pd.DataFrame:
    """Normalisasi kolom wilayah secara in-place dan kembalikan df."""
    for nama, jenis in kolom.items():
        if nama in df.columns:
            fungsi = NORMALISATOR[jenis]
            hasil = df[nama].map(fungsi).astype("string")
            if jenis == "kota":
                hasil = _rapikan_prefiks_kota(hasil)
            df[nama] = hasil
    return df
