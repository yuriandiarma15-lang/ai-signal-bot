"""
ENTRY REASON BANK
=================

XAU AI SIGNAL ENGINE
SMC EDUCATIONAL REASON BANK

Tujuan:
- Membuat alasan entry lebih manusiawi
- Memberikan edukasi pada setiap signal
- Menghindari alasan yang tidak sesuai kondisi market
- Tidak menggunakan alasan M1 rejection jika memang belum ada
- Tidak menggunakan alasan mitigation jika zona masih untouched
- Menyesuaikan BUY / SELL
- Menyesuaikan Order Block / FVG
- Menyesuaikan Pending / Market
- Menyesuaikan untouched / partial / full
- Menyesuaikan sesi trading

CATATAN:
Bank ini menggunakan deterministic random berdasarkan seed.
Artinya:
    signal yang sama -> alasan yang sama
    signal berbeda -> variasi dapat berbeda

Jangan menganggap probability sebagai jaminan profit.
"""


import random
from typing import Optional, List


# =========================================================
# HELPER
# =========================================================

def _choose(
    items: List[str],
    seed: Optional[str] = None,
) -> str:

    if not items:
        return ""

    if seed:
        rng = random.Random(str(seed))
        return rng.choice(items)

    return random.choice(items)


def _choose_many(
    items: List[str],
    count: int,
    seed: Optional[str] = None,
) -> List[str]:

    if not items:
        return []

    count = min(
        max(1, count),
        len(items),
    )

    if seed:
        rng = random.Random(str(seed))
        return rng.sample(items, count)

    return random.sample(items, count)


# =========================================================
# =========================================================
# BULLISH — ORDER BLOCK — PENDING
# =========================================================
# =========================================================

BULLISH_OB_PENDING = [

    "Struktur bullish mendukung retracement menuju Order Block demand.",

    "Order Block bullish berada di bawah harga dan masih berpotensi menjadi area mitigasi buyer.",

    "Harga masih mempertahankan struktur naik sehingga pullback menuju OB dapat menjadi area observasi.",

    "OB bullish yang masih fresh memberikan lokasi yang lebih terukur dibanding mengejar harga di tengah pergerakan.",

    "Zona demand berada pada posisi yang logis terhadap struktur bullish M5.",

    "Harga belum kembali menguji OB sehingga pending entry digunakan untuk menunggu retracement.",

    "Order Block bullish berfungsi sebagai area potensial tempat buyer sebelumnya menunjukkan aktivitas.",

    "Retracement menuju OB memberikan peluang mendapatkan harga entry yang lebih baik daripada mengejar momentum.",

    "Zona bullish belum menunjukkan mitigasi yang signifikan sehingga masih layak dipantau sebagai demand.",

    "Pending Buy Limit digunakan karena harga saat ini masih berada di atas area demand.",

    "Struktur harga belum menunjukkan alasan kuat untuk mengejar entry market pada level sekarang.",

    "OB bullish menjadi referensi untuk mencari re-entry jika harga melakukan pullback.",

    "Area demand dipilih berdasarkan hubungan antara struktur swing dan lokasi OB.",

    "Harga yang masih jauh dari OB membuat pending order lebih disiplin daripada entry langsung.",

    "Setup mengutamakan lokasi entry terlebih dahulu sebelum mempertimbangkan momentum.",

    "Order Block bullish memberikan area retracement yang lebih terstruktur untuk continuation.",

    "Buyer masih memiliki struktur pendukung sehingga area OB diperlakukan sebagai zona reaksi potensial.",

    "Pending order menunggu harga kembali ke area yang sebelumnya menunjukkan ketidakseimbangan supply dan demand.",

    "OB belum disentuh kembali sehingga validitas zona belum berkurang akibat mitigasi berulang.",

    "Entry ditempatkan di bawah harga karena sistem menunggu pullback ke demand, bukan mengejar candle bullish.",

]


# =========================================================
# BULLISH — FVG — PENDING
# =========================================================

BULLISH_FVG_PENDING = [

    "Bullish Fair Value Gap berada di bawah harga dan dapat menjadi area retracement.",

    "FVG bullish menunjukkan adanya imbalance yang terbentuk ketika harga bergerak cepat ke atas.",

    "Imbalance yang masih fresh memberikan area potensial untuk menunggu re-entry buyer.",

    "Harga belum kembali mengisi FVG sehingga pending entry digunakan untuk menunggu retracement.",

    "Bullish FVG menjadi referensi lokasi entry karena harga sebelumnya meninggalkan area tersebut dengan displacement.",

    "FVG memberikan lokasi entry yang lebih terukur dibanding mengejar harga setelah displacement.",

    "Area imbalance berada dalam arah yang sejalan dengan bias struktur M5.",

    "Pending Buy Limit digunakan untuk mengantisipasi retracement menuju imbalance bullish.",

    "FVG yang belum termitigasi masih memiliki relevansi sebagai area ketidakseimbangan harga.",

    "Harga sedang berada di atas FVG sehingga sistem menunggu pullback sebelum entry.",

    "Imbalance bullish menjadi area observasi karena struktur masih memberikan dukungan kepada buyer.",

    "Setup ini mengutamakan lokasi retracement daripada momentum jangka pendek.",

    "FVG bullish dapat menjadi area rebalancing sebelum harga melanjutkan struktur naik.",

    "Harga tidak dikejar pada level sekarang karena zona entry berada lebih rendah.",

    "Pending order memberikan kesempatan menunggu harga datang ke zona yang sudah ditentukan.",

    "FVG dipilih karena terbentuk dalam konteks displacement bullish yang mendukung struktur.",

    "Zona imbalance masih fresh sehingga sistem belum menganggapnya kehilangan validitas.",

    "Retracement ke FVG akan menjadi pengujian apakah buyer masih mempertahankan area tersebut.",

    "Area FVG digunakan sebagai lokasi potensial untuk mendapatkan entry dengan risiko yang lebih terukur.",

    "Entry menunggu harga masuk kembali ke imbalance sebelum mengambil keputusan.",

]


# =========================================================
# BEARISH — ORDER BLOCK — PENDING
# =========================================================

BEARISH_OB_PENDING = [

    "Struktur bearish mendukung retracement menuju Order Block supply.",

    "Order Block bearish berada di atas harga dan berpotensi menjadi area mitigasi seller.",

    "Harga masih mempertahankan struktur turun sehingga pullback menuju OB dapat menjadi area observasi.",

    "OB bearish yang masih fresh memberikan lokasi entry yang lebih terukur daripada mengejar harga turun.",

    "Zona supply berada pada posisi yang logis terhadap struktur bearish M5.",

    "Harga belum kembali menguji OB sehingga pending Sell Limit digunakan untuk menunggu retracement.",

    "Order Block bearish menjadi area potensial tempat seller sebelumnya menunjukkan aktivitas.",

    "Retracement menuju OB memberikan peluang mendapatkan harga entry yang lebih baik daripada mengejar momentum bearish.",

    "Zona supply belum menunjukkan mitigasi yang signifikan sehingga masih layak dipantau.",

    "Pending Sell Limit digunakan karena harga saat ini masih berada di bawah area supply.",

    "Struktur harga belum memberikan alasan kuat untuk mengejar entry market pada level sekarang.",

    "OB bearish menjadi referensi untuk mencari re-entry jika harga melakukan pullback.",

    "Area supply dipilih berdasarkan hubungan antara struktur swing dan lokasi Order Block.",

    "Harga yang masih jauh dari OB membuat pending order lebih disiplin daripada entry langsung.",

    "Setup mengutamakan lokasi entry sebelum mempertimbangkan momentum.",

    "Order Block bearish memberikan area retracement yang terstruktur untuk continuation.",

    "Seller masih memiliki dukungan struktur sehingga OB diperlakukan sebagai zona reaksi potensial.",

    "Pending order menunggu harga kembali ke area supply yang sebelumnya memicu displacement.",

    "OB belum disentuh kembali sehingga validitas zona belum berkurang akibat mitigasi berulang.",

    "Entry ditempatkan di atas harga karena sistem menunggu pullback ke supply.",

]


# =========================================================
# BEARISH — FVG — PENDING
# =========================================================

BEARISH_FVG_PENDING = [

    "Bearish Fair Value Gap berada di atas harga dan dapat menjadi area retracement.",

    "FVG bearish menunjukkan adanya imbalance yang terbentuk ketika harga bergerak cepat ke bawah.",

    "Imbalance bearish yang masih fresh memberikan area potensial untuk menunggu re-entry seller.",

    "Harga belum kembali mengisi FVG sehingga pending entry digunakan untuk menunggu retracement.",

    "Bearish FVG menjadi referensi lokasi entry karena harga sebelumnya meninggalkan area tersebut dengan displacement.",

    "FVG memberikan lokasi entry yang lebih terukur dibanding mengejar harga setelah displacement bearish.",

    "Area imbalance berada dalam arah yang sejalan dengan bias struktur M5.",

    "Pending Sell Limit digunakan untuk mengantisipasi retracement menuju imbalance bearish.",

    "FVG yang belum termitigasi masih memiliki relevansi sebagai area ketidakseimbangan harga.",

    "Harga sedang berada di bawah FVG sehingga sistem menunggu pullback sebelum entry.",

    "Imbalance bearish menjadi area observasi karena struktur masih memberikan dukungan kepada seller.",

    "Setup ini mengutamakan lokasi retracement daripada mengejar momentum.",

    "FVG bearish dapat menjadi area rebalancing sebelum harga melanjutkan struktur turun.",

    "Harga tidak dikejar pada level sekarang karena zona entry berada lebih tinggi.",

    "Pending order memberikan kesempatan menunggu harga datang ke zona yang sudah ditentukan.",

    "FVG dipilih karena terbentuk dalam konteks displacement bearish yang mendukung struktur.",

    "Zona imbalance masih fresh sehingga sistem belum menganggapnya kehilangan validitas.",

    "Retracement ke FVG akan menjadi pengujian apakah seller masih mempertahankan area tersebut.",

    "Area FVG digunakan sebagai lokasi potensial untuk mendapatkan entry dengan risiko yang lebih terukur.",

    "Entry menunggu harga masuk kembali ke imbalance sebelum mengambil keputusan.",

]


# =========================================================
# BULLISH MARKET
# =========================================================

BULLISH_MARKET = [

    "Buyer menunjukkan rejection di sekitar demand sehingga entry market mendapatkan konfirmasi tambahan.",

    "Rejection bullish pada M1 menunjukkan seller mulai kehilangan tekanan di area demand.",

    "Harga telah melakukan retest zona dan buyer mulai memberikan respons.",

    "M1 memberikan konfirmasi bahwa harga tidak mampu bertahan di bawah area demand.",

    "Reaksi bullish setelah retest memberikan konfirmasi tambahan untuk continuation.",

    "Buyer kembali aktif setelah harga memasuki area SMC.",

    "Entry market dipilih setelah lokasi zona tidak lagi hanya menjadi asumsi, tetapi sudah mendapatkan respons harga.",

    "Rejection M1 membantu membedakan retracement biasa dari kemungkinan continuation bullish.",

    "Harga menunjukkan respons positif setelah menyentuh area demand.",

    "Konfirmasi M1 memberikan timing entry yang lebih presisi dibanding langsung masuk ketika zona pertama kali ditemukan.",

    "Seller gagal mempertahankan tekanan setelah harga memasuki zona bullish.",

    "Momentum jangka pendek mulai kembali searah dengan struktur bullish M5.",

    "Market entry digunakan karena harga sudah memberikan reaksi dari area yang sebelumnya dipantau.",

    "Rejection pada zona meningkatkan kualitas timing tanpa mengubah dasar analisa struktur M5.",

    "Buyer menunjukkan respons setelah liquidity berada di sekitar area demand.",

    "Entry mengikuti reaksi harga setelah retest, bukan sekadar mengandalkan prediksi arah.",

    "Konfirmasi M1 memberikan bukti tambahan bahwa demand masih mendapatkan respons.",

    "Harga berhasil bertahan di sekitar zona dan mulai bergerak kembali mengikuti bias bullish.",

    "Setup menunjukkan perpaduan antara struktur M5 dan konfirmasi timing M1.",

    "Market entry digunakan karena retracement sudah menghasilkan respons bullish yang terlihat pada M1.",

]


# =========================================================
# BEARISH MARKET
# =========================================================

BEARISH_MARKET = [

    "Seller menunjukkan rejection di sekitar supply sehingga entry market mendapatkan konfirmasi tambahan.",

    "Rejection bearish pada M1 menunjukkan buyer mulai kehilangan tekanan di area supply.",

    "Harga telah melakukan retest zona dan seller mulai memberikan respons.",

    "M1 memberikan konfirmasi bahwa harga tidak mampu bertahan di atas area supply.",

    "Reaksi bearish setelah retest memberikan konfirmasi tambahan untuk continuation.",

    "Seller kembali aktif setelah harga memasuki area SMC.",

    "Entry market dipilih setelah zona mendapatkan respons harga yang mendukung bias bearish.",

    "Rejection M1 membantu membedakan retracement biasa dari kemungkinan continuation bearish.",

    "Harga menunjukkan respons negatif setelah menyentuh area supply.",

    "Konfirmasi M1 memberikan timing entry yang lebih presisi daripada langsung masuk ketika zona pertama kali ditemukan.",

    "Buyer gagal mempertahankan tekanan setelah harga memasuki zona bearish.",

    "Momentum jangka pendek mulai kembali searah dengan struktur bearish M5.",

    "Market entry digunakan karena harga sudah memberikan reaksi dari area yang sebelumnya dipantau.",

    "Rejection pada zona meningkatkan kualitas timing tanpa mengubah dasar analisa struktur M5.",

    "Seller menunjukkan respons setelah liquidity berada di sekitar area supply.",

    "Entry mengikuti reaksi harga setelah retest, bukan sekadar mengandalkan prediksi arah.",

    "Konfirmasi M1 memberikan bukti tambahan bahwa supply masih mendapatkan respons.",

    "Harga gagal bertahan di sekitar zona dan mulai bergerak kembali mengikuti bias bearish.",

    "Setup menunjukkan perpaduan antara struktur M5 dan konfirmasi timing M1.",

    "Market entry digunakan karena retracement sudah menghasilkan respons bearish yang terlihat pada M1.",

]


# =========================================================
# BULLISH PARTIAL FVG
# =========================================================

BULLISH_PARTIAL = [

    "FVG bullish baru terisi sebagian sehingga retracement masih berpotensi berlanjut.",

    "Imbalance belum sepenuhnya termitigasi sehingga entry agresif belum disarankan.",

    "Partial fill menunjukkan harga sudah memasuki FVG tetapi belum memberikan konfirmasi penuh.",

    "Harga sudah menyentuh sebagian imbalance, namun respons buyer belum cukup kuat.",

    "Partial fill membuat area FVG masih membutuhkan validasi tambahan sebelum entry market.",

    "Masuk terlalu cepat pada FVG yang baru terisi sebagian dapat membuat trader terkena retracement lanjutan.",

    "Sistem memilih menunggu karena harga belum memberikan reaksi yang cukup jelas dari imbalance.",

    "FVG masih dalam proses mitigasi sehingga keputusan entry perlu menunggu struktur timing yang lebih jelas.",

    "Partial fill belum dapat dianggap sebagai rejection bullish.",

    "Harga baru memasuki sebagian area imbalance sehingga belum ada bukti kuat bahwa retracement telah selesai.",

    "Kondisi ini mengajarkan pentingnya membedakan touch zona dengan rejection zona.",

    "FVG partial lebih baik dipantau daripada dipaksakan menjadi market entry.",

]


# =========================================================
# BEARISH PARTIAL FVG
# =========================================================

BEARISH_PARTIAL = [

    "FVG bearish baru terisi sebagian sehingga retracement masih berpotensi berlanjut.",

    "Imbalance belum sepenuhnya termitigasi sehingga entry agresif belum disarankan.",

    "Partial fill menunjukkan harga sudah memasuki FVG tetapi belum memberikan konfirmasi penuh.",

    "Harga sudah menyentuh sebagian imbalance, namun respons seller belum cukup kuat.",

    "Partial fill membuat area FVG masih membutuhkan validasi tambahan sebelum entry market.",

    "Masuk terlalu cepat pada FVG yang baru terisi sebagian dapat membuat trader terkena retracement lanjutan.",

    "Sistem memilih menunggu karena harga belum memberikan reaksi yang cukup jelas dari imbalance.",

    "FVG masih dalam proses mitigasi sehingga keputusan entry perlu menunggu struktur timing yang lebih jelas.",

    "Partial fill belum dapat dianggap sebagai rejection bearish.",

    "Harga baru memasuki sebagian area imbalance sehingga belum ada bukti kuat bahwa retracement telah selesai.",

    "Kondisi ini mengajarkan pentingnya membedakan touch zona dengan rejection zona.",

    "FVG partial lebih baik dipantau daripada dipaksakan menjadi market entry.",

]


# =========================================================
# FRESH ZONE EDUCATION
# =========================================================

FRESH_ZONE_NOTES = [

    "Zona fresh berarti area tersebut belum banyak diuji oleh harga sehingga respons berikutnya tetap perlu dikonfirmasi.",

    "Zona yang belum disentuh bukan berarti pasti berhasil; fresh zone hanya menunjukkan bahwa mitigasi sebelumnya masih minimal.",

    "Pending entry membantu menjaga disiplin karena trader tidak perlu mengejar harga yang sudah bergerak menjauh dari zona.",

    "Fresh zone sebaiknya diperlakukan sebagai area minat, bukan kepastian reversal.",

    "Semakin sedikit mitigasi sebelumnya, semakin penting melihat bagaimana harga bereaksi ketika pertama kali kembali ke zona.",

    "Konsep fresh zone mengajarkan bahwa lokasi entry sering sama pentingnya dengan arah market.",

    "Menunggu retracement ke zona membantu menjaga rasio risiko tetap lebih terukur.",

    "Tidak semua fresh zone akan menghasilkan reversal; struktur yang mendukung tetap menjadi filter utama.",

]


# =========================================================
# FULL MITIGATION — BULLISH
# =========================================================

BULLISH_FULL_NOTES = [

    "Zona sudah mengalami mitigasi sehingga entry tidak lagi diperlakukan sebagai fresh-zone setup.",

    "Karena harga telah kembali menguji zona, konfirmasi M1 menjadi lebih penting sebelum mengambil entry.",

    "Mitigasi menunjukkan bahwa sebagian liquidity atau order di area tersebut kemungkinan sudah terserap.",

    "Zona yang sudah termitigasi tetap dapat menghasilkan reaksi, tetapi kualitasnya berbeda dari zona fresh.",

    "Entry setelah mitigation sebaiknya mengikuti respons harga, bukan hanya mengandalkan keberadaan zona.",

    "Kondisi ini mengajarkan bahwa touch zona dan rejection zona adalah dua hal yang berbeda.",

]


# =========================================================
# FULL MITIGATION — BEARISH
# =========================================================

BEARISH_FULL_NOTES = [

    "Zona sudah mengalami mitigasi sehingga entry tidak lagi diperlakukan sebagai fresh-zone setup.",

    "Karena harga telah kembali menguji zona, konfirmasi M1 menjadi lebih penting sebelum mengambil entry.",

    "Mitigasi menunjukkan bahwa sebagian liquidity atau order di area tersebut kemungkinan sudah terserap.",

    "Zona yang sudah termitigasi tetap dapat menghasilkan reaksi, tetapi kualitasnya berbeda dari zona fresh.",

    "Entry setelah mitigation sebaiknya mengikuti respons harga, bukan hanya mengandalkan keberadaan zona.",

    "Kondisi ini mengajarkan bahwa touch zona dan rejection zona adalah dua hal yang berbeda.",

]


# =========================================================
# M1 BULLISH EDUCATION
# =========================================================

M1_BULLISH_NOTES = [

    "M1 digunakan sebagai timing entry, bukan sebagai pengganti struktur M5.",

    "Rejection bullish pada M1 menunjukkan bahwa buyer mulai merespons area yang sebelumnya ditentukan oleh struktur M5.",

    "Konfirmasi M1 membantu mengurangi risiko masuk terlalu cepat ketika harga masih melakukan retracement.",

    "Rejection yang muncul di zona lebih berarti dibanding rejection yang terjadi jauh dari zona SMC.",

    "M1 memberikan informasi tentang respons jangka pendek setelah harga mencapai area yang sudah dianalisa.",

    "Entry menjadi lebih terukur ketika struktur M5 dan reaksi M1 memberikan arah yang sama.",

    "M1 confirmation bukan jaminan harga akan naik; fungsinya adalah meningkatkan kualitas timing.",

    "Trader perlu membedakan candle bullish biasa dengan rejection yang benar-benar terjadi di area demand.",

]


# =========================================================
# M1 BEARISH EDUCATION
# =========================================================

M1_BEARISH_NOTES = [

    "M1 digunakan sebagai timing entry, bukan sebagai pengganti struktur M5.",

    "Rejection bearish pada M1 menunjukkan bahwa seller mulai merespons area yang sebelumnya ditentukan oleh struktur M5.",

    "Konfirmasi M1 membantu mengurangi risiko masuk terlalu cepat ketika harga masih melakukan retracement.",

    "Rejection yang muncul di zona lebih berarti dibanding rejection yang terjadi jauh dari zona SMC.",

    "M1 memberikan informasi tentang respons jangka pendek setelah harga mencapai area yang sudah dianalisa.",

    "Entry menjadi lebih terukur ketika struktur M5 dan reaksi M1 memberikan arah yang sama.",

    "M1 confirmation bukan jaminan harga akan turun; fungsinya adalah meningkatkan kualitas timing.",

    "Trader perlu membedakan candle bearish biasa dengan rejection yang benar-benar terjadi di area supply.",

]


# =========================================================
# BOS EDUCATION
# =========================================================

BOS_BULLISH = [

    "BOS bullish menunjukkan bahwa swing high sebelumnya berhasil ditembus sehingga struktur memberikan dukungan kepada buyer.",

    "Break of Structure bullish menjadi konfirmasi bahwa harga berhasil membuat ekspansi ke sisi atas struktur.",

    "BOS tidak berdiri sendiri; kualitas setup tetap bergantung pada lokasi zona dan respons harga setelah breakout.",

    "BOS bullish membantu menentukan arah struktur, sedangkan M1 digunakan untuk menentukan timing entry.",

    "Breakout struktur perlu dibaca bersama liquidity karena breakout yang terjadi setelah sweep dapat memberikan konteks yang lebih kuat.",

    "BOS bullish menjadi alasan struktural, bukan jaminan bahwa setiap retracement akan langsung naik.",

]


BOS_BEARISH = [

    "BOS bearish menunjukkan bahwa swing low sebelumnya berhasil ditembus sehingga struktur memberikan dukungan kepada seller.",

    "Break of Structure bearish menjadi konfirmasi bahwa harga berhasil melakukan ekspansi ke sisi bawah struktur.",

    "BOS tidak berdiri sendiri; kualitas setup tetap bergantung pada lokasi zona dan respons harga setelah breakout.",

    "BOS bearish membantu menentukan arah struktur, sedangkan M1 digunakan untuk menentukan timing entry.",

    "Breakout struktur perlu dibaca bersama liquidity karena breakout setelah sweep dapat memberikan konteks yang lebih kuat.",

    "BOS bearish menjadi alasan struktural, bukan jaminan bahwa setiap retracement akan langsung turun.",

]


# =========================================================
# CHOCH EDUCATION
# =========================================================

CHOCH_BULLISH = [

    "CHoCH bullish menunjukkan adanya perubahan karakter harga dari tekanan bearish menuju struktur yang mulai mendukung buyer.",

    "Perubahan karakter perlu dikonfirmasi dengan lokasi zona dan reaksi harga sebelum entry.",

    "CHoCH membantu membaca kemungkinan perubahan arah, tetapi tidak boleh dianggap sebagai sinyal tunggal.",

    "Ketika CHoCH muncul dekat liquidity sweep dan demand, konteks reversal menjadi lebih menarik untuk dipantau.",

    "CHoCH memberikan peringatan awal perubahan struktur, sementara M1 membantu menentukan timing.",

]


CHOCH_BEARISH = [

    "CHoCH bearish menunjukkan adanya perubahan karakter harga dari tekanan bullish menuju struktur yang mulai mendukung seller.",

    "Perubahan karakter perlu dikonfirmasi dengan lokasi zona dan reaksi harga sebelum entry.",

    "CHoCH membantu membaca kemungkinan perubahan arah, tetapi tidak boleh dianggap sebagai sinyal tunggal.",

    "Ketika CHoCH muncul dekat liquidity sweep dan supply, konteks reversal menjadi lebih menarik untuk dipantau.",

    "CHoCH memberikan peringatan awal perubahan struktur, sementara M1 membantu menentukan timing.",

]


# =========================================================
# LIQUIDITY
# =========================================================

LIQUIDITY_BULLISH = [

    "Liquidity sweep di bawah area low dapat menjadi konteks penting ketika harga kemudian menunjukkan respons bullish.",

    "Stop hunt sebelum pergerakan bullish dapat menunjukkan bahwa liquidity sisi bawah telah diambil sebelum ekspansi.",

    "Liquidity sweep bukan sinyal buy secara otomatis; yang lebih penting adalah respons harga setelah liquidity diambil.",

    "Pengambilan liquidity di bawah swing low menjadi lebih relevan ketika diikuti displacement bullish.",

    "Konteks liquidity membantu menjelaskan mengapa harga melakukan spike sebelum kembali mengikuti bias struktur.",

    "Setup memperhatikan kemungkinan bahwa seller terlambat masuk setelah liquidity bawah tersapu.",

]


LIQUIDITY_BEARISH = [

    "Liquidity sweep di atas area high dapat menjadi konteks penting ketika harga kemudian menunjukkan respons bearish.",

    "Stop hunt sebelum pergerakan bearish dapat menunjukkan bahwa liquidity sisi atas telah diambil sebelum ekspansi.",

    "Liquidity sweep bukan sinyal sell secara otomatis; yang lebih penting adalah respons harga setelah liquidity diambil.",

    "Pengambilan liquidity di atas swing high menjadi lebih relevan ketika diikuti displacement bearish.",

    "Konteks liquidity membantu menjelaskan mengapa harga melakukan spike sebelum kembali mengikuti bias struktur.",

    "Setup memperhatikan kemungkinan bahwa buyer terlambat masuk setelah liquidity atas tersapu.",

]


# =========================================================
# GENERAL EDUCATION
# =========================================================

GENERAL_REASONS = [

    "Setup menggabungkan struktur M5 dengan timing M1 sehingga arah dan lokasi entry tidak dibaca secara terpisah.",

    "SMC digunakan untuk mencari lokasi penting, sedangkan price action digunakan untuk membaca respons harga di lokasi tersebut.",

    "Entry tidak hanya bergantung pada arah market tetapi juga pada posisi harga terhadap zona.",

    "Risk management tetap menjadi bagian penting karena setup dengan struktur bagus sekalipun tetap memiliki kemungkinan gagal.",

    "Sinyal ini sebaiknya dipahami sebagai skenario dengan probabilitas, bukan kepastian arah harga.",

    "Kualitas entry tidak hanya ditentukan oleh jumlah konfluensi tetapi juga oleh lokasi dan timing.",

    "Trader sebaiknya menunggu harga datang ke area yang direncanakan daripada mengejar pergerakan yang sudah jauh.",

    "Struktur memberikan konteks, zona memberikan lokasi, dan M1 memberikan timing.",

    "Tidak ada satu konsep SMC yang seharusnya digunakan sendirian tanpa melihat konteks market.",

    "Validasi setup dilakukan dengan menggabungkan beberapa informasi yang saling mendukung.",

    "Semakin banyak konfluensi yang searah, semakin kuat alasan untuk mempertimbangkan setup, tetapi tetap bukan jaminan profit.",

    "Setup dipilih berdasarkan hubungan antara market structure, liquidity, imbalance, dan price reaction.",

]


# =========================================================
# SESSION NOTES
# =========================================================

SESSION_NOTES = {

    "Asian Session": [

        "Sesi Asia cenderung membentuk range awal yang dapat menjadi referensi liquidity untuk sesi berikutnya.",

        "High dan low sesi Asia sering menjadi area yang diperhatikan ketika London mulai meningkatkan volatilitas.",

        "Volatilitas Asia dapat lebih tenang sehingga struktur dan zona lebih penting daripada mengejar momentum.",

        "Jika range Asia masih sempit, breakout berikutnya perlu dibaca bersama liquidity dan displacement.",

        "Jangan menganggap breakout kecil di sesi Asia sebagai continuation sebelum ada struktur yang mendukung.",

        "Sesi Asia sering menjadi fase pembentukan liquidity pool sebelum sesi Eropa aktif.",

        "Perhatikan apakah harga bertahan di dalam range atau mulai melakukan ekspansi dari range Asia.",

        "Kondisi range membuat trader perlu lebih selektif terhadap entry karena false breakout dapat lebih sering terjadi.",

        "High dan low Asia dapat digunakan sebagai referensi untuk membaca kemungkinan liquidity sweep.",

        "Pada sesi yang relatif tenang, menunggu harga mencapai zona lebih baik daripada mengejar candle.",

        "Jika struktur M5 masih ranging, setup perlu diperlakukan lebih konservatif sampai displacement terlihat.",

        "Pelajaran penting sesi Asia adalah memahami range sebelum mencari breakout.",

    ],

    "London Session": [

        "Pembukaan London sering meningkatkan volatilitas sehingga liquidity sweep dapat muncul sebelum arah utama terlihat.",

        "Perhatikan high dan low Asia karena keduanya dapat menjadi target liquidity ketika London mulai aktif.",

        "False breakout pada awal London perlu dibedakan dari displacement yang benar-benar mengubah struktur.",

        "London sering menjadi fase penting untuk validasi BOS atau CHoCH setelah liquidity Asia diambil.",

        "Jangan langsung mengejar candle besar saat London open; tunggu lokasi dan struktur yang lebih jelas.",

        "Jika liquidity Asia sudah tersapu, respons berikutnya dapat membantu membaca arah pergerakan selanjutnya.",

        "Volatilitas London membuat kualitas timing M1 menjadi lebih penting.",

        "Retracement ke OB atau FVG setelah displacement London dapat memberikan lokasi entry yang lebih terukur.",

        "Pergerakan cepat tidak selalu berarti continuation; liquidity dan struktur tetap perlu diperiksa.",

        "Sesi London mengajarkan pentingnya menunggu konfirmasi setelah volatility expansion.",

        "Jika harga sudah terlalu jauh dari zona, kualitas risk-reward dapat menurun meskipun arah market benar.",

        "Gunakan momentum London sebagai informasi, bukan alasan untuk mengabaikan risk management.",

    ],

    "New York Session": [

        "Masuknya liquidity New York dapat meningkatkan volatilitas XAUUSD sehingga pergerakan perlu dibaca dengan lebih disiplin.",

        "High dan low sebelumnya dapat menjadi target liquidity ketika sesi New York mulai aktif.",

        "News Amerika dapat menyebabkan spike sehingga entry sebaiknya tetap mengikuti zona dan risk management.",

        "Displacement yang muncul setelah liquidity sweep dapat memberikan konteks penting untuk membaca continuation atau reversal.",

        "Jangan menyamakan candle besar dengan sinyal valid; lokasi candle terhadap struktur tetap lebih penting.",

        "M1 confirmation menjadi semakin berguna ketika volatilitas meningkat.",

        "Jika harga bergerak terlalu cepat menjauh dari zona, menunggu retracement dapat lebih rasional daripada mengejar entry.",

        "Sesi New York sering menghasilkan ekspansi range yang membutuhkan pengelolaan risiko lebih disiplin.",

        "Perhatikan reaksi harga setelah liquidity diambil sebelum menyimpulkan arah.",

        "Kondisi volatil membuat stop loss yang terlalu dekat lebih mudah terkena noise.",

        "Setup yang memiliki struktur jelas tetap membutuhkan perhatian terhadap event ekonomi besar.",

        "Pelajaran utama sesi New York adalah membedakan displacement dengan volatility spike sementara.",

    ],

    "New York Late": [

        "Sesi akhir New York perlu lebih waspada terhadap exhaustion setelah pergerakan besar.",

        "Setelah volatility spike, retracement dapat menjadi lebih dominan daripada continuation.",

        "Jika harga sudah bergerak jauh dari zona, mengejar entry dapat membuat risk-reward menjadi kurang menarik.",

        "Perhatikan apakah struktur masih menghasilkan swing baru atau mulai kehilangan momentum.",

        "Late session membutuhkan selektivitas lebih tinggi karena liquidity dan momentum dapat berubah.",

        "Setup yang belum mendapatkan konfirmasi sebaiknya tidak dipaksakan hanya karena market masih bergerak.",

        "Kondisi akhir sesi mengajarkan pentingnya mengetahui kapan tidak melakukan entry.",

        "Jika displacement sudah terlalu jauh, menunggu retracement ke zona biasanya lebih disiplin.",

        "Waspadai reversal setelah pergerakan panjang yang tidak lagi didukung struktur baru.",

        "Trader perlu membedakan continuation yang sehat dari pergerakan akhir sesi yang mulai kehilangan tenaga.",

    ],

    "Trading": [

        "Market sedang berada di luar kategori sesi khusus sehingga struktur dan zona tetap menjadi acuan utama.",

        "Fokus utama tetap pada hubungan antara market structure, liquidity, zona SMC, dan timing.",

        "Kondisi market perlu dibaca berdasarkan price action aktual, bukan asumsi bahwa sesi tertentu selalu bergerak dengan cara yang sama.",

        "Risk management tetap menjadi filter utama dalam setiap kondisi sesi.",

        "Jika harga tidak berada pada lokasi yang direncanakan, tidak ada kewajiban untuk mengejar entry.",

    ],
}


# =========================================================
# CONTEXTUAL ADDITION
# =========================================================

def _contextual_reasons(
    bias: str,
    zone_type: str,
    is_pending: bool,
    fill_status: str,
) -> List[str]:

    result = []

    zone = (zone_type or "").lower()

    # -----------------------------------------------------
    # BIAS
    # -----------------------------------------------------

    if bias == "bullish":

        result.extend(
            BOS_BULLISH
        )

        result.extend(
            LIQUIDITY_BULLISH
        )

    elif bias == "bearish":

        result.extend(
            BOS_BEARISH
        )

        result.extend(
            LIQUIDITY_BEARISH
        )

    # -----------------------------------------------------
    # ZONE
    # -----------------------------------------------------

    if "order block" in zone:

        if bias == "bullish":

            result.extend(
                BULLISH_OB_PENDING
            )

        elif bias == "bearish":

            result.extend(
                BEARISH_OB_PENDING
            )

    elif "fair value gap" in zone:

        if bias == "bullish":

            result.extend(
                BULLISH_FVG_PENDING
            )

        elif bias == "bearish":

            result.extend(
                BEARISH_FVG_PENDING
            )

    # -----------------------------------------------------
    # FILL STATUS
    # -----------------------------------------------------

    if fill_status == "untouched":

        result.extend(
            FRESH_ZONE_NOTES
        )

    elif fill_status == "full":

        if bias == "bullish":

            result.extend(
                BULLISH_FULL_NOTES
            )

        else:

            result.extend(
                BEARISH_FULL_NOTES
            )

    # -----------------------------------------------------
    # MARKET
    # -----------------------------------------------------

    if not is_pending:

        if bias == "bullish":

            result.extend(
                BULLISH_MARKET
            )

            result.extend(
                M1_BULLISH_NOTES
            )

        elif bias == "bearish":

            result.extend(
                BEARISH_MARKET
            )

            result.extend(
                M1_BEARISH_NOTES
            )

    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------

    if is_pending:

        result.extend(
            FRESH_ZONE_NOTES
        )

    return result


# =========================================================
# GET ENTRY REASON
# =========================================================

def get_entry_reason(
    bias: str,
    zone_type: Optional[str],
    is_pending: bool,
    fill_status: str,
    seed: Optional[str] = None,
) -> str:

    bias = (
        bias or ""
    ).lower()

    zone_type = (
        zone_type or ""
    ).lower()

    fill_status = (
        fill_status or "untouched"
    ).lower()

    # =====================================================
    # PARTIAL FVG
    # =====================================================

    if (
        "fair value gap" in zone_type
        and fill_status == "partial"
    ):

        if bias == "bullish":

            return _choose(
                BULLISH_PARTIAL,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_PARTIAL,
                seed,
            )

    # =====================================================
    # MARKET
    # =====================================================

    if not is_pending:

        if bias == "bullish":

            return _choose(
                BULLISH_MARKET,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_MARKET,
                seed,
            )

    # =====================================================
    # PENDING OB
    # =====================================================

    if (
        is_pending
        and "order block" in zone_type
    ):

        if bias == "bullish":

            return _choose(
                BULLISH_OB_PENDING,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_OB_PENDING,
                seed,
            )

    # =====================================================
    # PENDING FVG
    # =====================================================

    if (
        is_pending
        and "fair value gap" in zone_type
    ):

        if bias == "bullish":

            return _choose(
                BULLISH_FVG_PENDING,
                seed,
            )

        if bias == "bearish":

            return _choose(
                BEARISH_FVG_PENDING,
                seed,
            )

    # =====================================================
    # FALLBACK
    # =====================================================

    return _choose(
        GENERAL_REASONS,
        seed,
    )


# =========================================================
# EDUCATIONAL NOTE
# =========================================================

def get_educational_note(
    bias: str,
    zone_type: Optional[str],
    is_pending: bool,
    fill_status: str,
    m1_confirmation: bool = False,
    seed: Optional[str] = None,
) -> str:

    bias = (
        bias or ""
    ).lower()

    zone = (
        zone_type or ""
    ).lower()

    notes = []

    # -----------------------------------------------------
    # ZONE
    # -----------------------------------------------------

    if fill_status == "untouched":

        notes.extend(
            FRESH_ZONE_NOTES
        )

    elif fill_status == "partial":

        if "fair value gap" in zone:

            if bias == "bullish":

                notes.extend(
                    BULLISH_PARTIAL
                )

            elif bias == "bearish":

                notes.extend(
                    BEARISH_PARTIAL
                )

    elif fill_status == "full":

        if bias == "bullish":

            notes.extend(
                BULLISH_FULL_NOTES
            )

        elif bias == "bearish":

            notes.extend(
                BEARISH_FULL_NOTES
            )

    # -----------------------------------------------------
    # M1
    # -----------------------------------------------------

    if m1_confirmation:

        if bias == "bullish":

            notes.extend(
                M1_BULLISH_NOTES
            )

        elif bias == "bearish":

            notes.extend(
                M1_BEARISH_NOTES
            )

    # -----------------------------------------------------
    # GENERAL
    # -----------------------------------------------------

    notes.extend(
        GENERAL_REASONS
    )

    if not notes:

        return ""

    return _choose(
        notes,
        seed,
    )


# =========================================================
# SESSION EXTRA NOTE
# =========================================================

def get_session_extra_note(
    session_name: str,
    seed: Optional[str] = None,
) -> str:

    notes = SESSION_NOTES.get(
        session_name,
        SESSION_NOTES.get(
            "Trading",
            [],
        ),
    )

    return _choose(
        notes,
        seed,
    )


# =========================================================
# GET MULTIPLE EDUCATIONAL REASONS
# =========================================================

def get_educational_reasons(
    bias: str,
    zone_type: Optional[str],
    is_pending: bool,
    fill_status: str,
    m1_confirmation: bool = False,
    count: int = 3,
    seed: Optional[str] = None,
) -> List[str]:

    """
    Mengambil beberapa alasan edukatif
    yang tetap sesuai konteks signal.

    Tidak menjamin semua alasan berasal
    dari kategori berbeda, tetapi semuanya
    tetap disaring berdasarkan kondisi signal.
    """

    contextual = _contextual_reasons(
        bias=bias,
        zone_type=zone_type or "",
        is_pending=is_pending,
        fill_status=fill_status,
    )

    if not contextual:

        contextual = GENERAL_REASONS

    # Hapus duplicate
    contextual = list(
        dict.fromkeys(
            contextual
        )
    )

    return _choose_many(
        contextual,
        count,
        seed,
    )


# =========================================================
# COMPATIBILITY
# =========================================================

def get_reason(
    bias: str,
    zone_type: Optional[str] = None,
    is_pending: bool = False,
    fill_status: str = "untouched",
    seed: Optional[str] = None,
) -> str:

    return get_entry_reason(
        bias=bias,
        zone_type=zone_type,
        is_pending=is_pending,
        fill_status=fill_status,
        seed=seed,
    )
