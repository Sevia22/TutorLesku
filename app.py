import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# --- KONFIGURASI DATABASE ---
def init_db():
    conn = sqlite3.connect('tutor_admin.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sesi_les (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT,
            nama_siswa TEXT,
            materi TEXT,
            durasi REAL,
            tarif_per_jam INTEGER,
            tagihan REAL,
            status_bayar TEXT
        )
    ''')
    conn.commit()
    conn.close()

def tambah_sesi(tanggal, nama_siswa, materi, durasi, tarif):
    tagihan = durasi * tarif
    conn = sqlite3.connect('tutor_admin.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO sesi_les (tanggal, nama_siswa, materi, durasi, tarif_per_jam, tagihan, status_bayar)
        VALUES (?, ?, ?, ?, ?, ?, 'Belum Dibayar')
    ''', (tanggal, nama_siswa, materi, durasi, tarif, tagihan))
    conn.commit()
    conn.close()

def ambil_semua_sesi():
    conn = sqlite3.connect('tutor_admin.db')
    df = pd.read_sql_query("SELECT * FROM sesi_les ORDER BY tanggal DESC", conn)
    conn.close()
    return df

def update_status_bayar(id_sesi, status_baru):
    conn = sqlite3.connect('tutor_admin.db')
    c = conn.cursor()
    c.execute("UPDATE sesi_les SET status_bayar = ? WHERE id = ?", (status_baru, id_sesi))
    conn.commit()
    conn.close()

# --- FUNGSI GENERATE HTML KE PDF ---
# Menggunakan WeasyPrint untuk menghasilkan tampilan PDF komersial yang rapi
def generate_pdf_report(df, total_durasi, total_tagihan):
    # Menyusun tabel baris demi baris ke dalam dokumen HTML
    rows_html = ""
    for idx, row in df.iterrows():
        rows_html += f"""
        <tr>
            <td style="text-align: center;">{idx+1}</td>
            <td>{row['tanggal']}</td>
            <td>{row['nama_siswa']} - {row['materi']}</td>
            <td style="text-align: center;">{row['durasi']} Jam</td>
            <td style="text-align: right;">Rp {row['tagihan']:,}</td>
            <td style="text-align: center;"><span style="background-color: #feebc8; color: #c05621; padding: 2px 6px; border-radius: 4px; font-size: 9pt; font-weight: bold;">{row['status_bayar']}</span></td>
        </tr>
        """

    html_template = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 20mm 15mm; }}
            body {{ font-family: Arial, sans-serif; color: #2d3748; line-height: 1.5; }}
            header {{ border-bottom: 2px solid #2b6cb0; padding-bottom: 10px; margin-bottom: 20px; }}
            .title {{ font-size: 20pt; color: #2b6cb0; font-weight: bold; }}
            .section {{ font-size: 13pt; color: #2b6cb0; border-left: 4px solid #2b6cb0; padding-left: 8px; margin: 20px 0 10px 0; font-weight: bold; }}
            .summary {{ background-color: #ebf8ff; border: 1px solid #bee3f8; padding: 15px; border-radius: 6px; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background-color: #2b6cb0; color: white; padding: 8px; font-size: 10pt; border: 1px solid #2b6cb0; }}
            td {{ padding: 8px; font-size: 10pt; border: 1px solid #e2e8f0; }}
            tr:nth-child(even) {{ background-color: #f7fafc; }}
        </style>
    </head>
    <body>
        <header>
            <div class="title">LAPORAN ADMINISTRASI SESI LES</div>
            <div>Dicetak pada: {datetime.now().strftime('%d %b %Y, %H:%M')}</div>
        </header>
        
        <div class="section">Ringkasan Estimasi Tagihan</div>
        <div class="summary">
            <table>
                <tr><td>Total Sesi Terlaksana:</td><td style="text-align: right; font-weight: bold;">{len(df)} Sesi</td></tr>
                <tr><td>Total Durasi Mengajar:</td><td style="text-align: right; font-weight: bold;">{total_durasi} Jam</td></tr>
                <tr style="font-size: 12pt; color: #2b6cb0; font-weight: bold;">
                    <td>Estimasi Total Tagihan:</td><td style="text-align: right;">Rp {total_tagihan:,}</td>
                </tr>
            </table>
        </div>

        <div class="section">Riwayat Sesi Lengkap</div>
        <table>
            <thead>
                <tr>
                    <th>No</th>
                    <th>Tanggal & Waktu</th>
                    <th>Siswa & Materi</th>
                    <th>Durasi</th>
                    <th>Tagihan</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    
    # Simpan file html sementara lalu konversi ke PDF menggunakan weasyprint
    with open("temp_report.html", "w", encoding="utf-8") as f:
        f.write(html_template)
        
    from weasyprint import HTML
    HTML("temp_report.html").write_pdf("Laporan_Sesi_Les.pdf")
    
    with open("Laporan_Sesi_Les.pdf", "rb") as pdf_file:
        pdf_bytes = pdf_file.read()
        
    return pdf_bytes


# --- INTERFACE APLIKASI UTAMA (STREAMLIT) ---
def main():
    init_db()
    st.set_page_config(page_title="Asisten Administrasi Tutor Les", layout="wide")
    
    st.title("📚 Asisten Administrasi Mengajar & Tagihan Tutor")
    st.write("Catat sesi les, pantau estimasi pendapatan, dan unduh laporan PDF dengan praktis.")
    st.hr()

    # Membagi layout menjadi 2 kolom (Kiri: Input data | Kanan: Dashboard & Riwayat)
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("📝 Catat Sesi Baru")
        with st.form("form_sesi", clear_on_submit=True):
            tgl = st.date_input("Tanggal Sesi", datetime.now())
            waktu = st.time_input("Waktu Sesi", datetime.now().time())
            nama_siswa = st.text_input("Nama Siswa", placeholder="Contoh: Rian")
            materi = st.text_input("Materi Pembelajaran", placeholder="Contoh: Aljabar Dasar")
            durasi = st.number_input("Durasi Sesi (Dalam Jam)", min_value=0.5, max_value=8.0, step=0.5, value=1.5)
            tarif = st.number_input("Tarif Mengajar per Jam (Rp)", min_value=10000, step=5000, value=100000)
            
            submit_btn = st.form_submit_button("Simpan Sesi")
            
            if submit_btn:
                if nama_siswa and materi:
                    gabung_tgl_waktu = f"{tgl.strftime('%d %b %Y')}, {waktu.strftime('%H:%M')}"
                    tambah_sesi(gabung_tgl_waktu, nama_siswa, materi, durasi, tarif)
                    st.success("Sesi berhasil direkam tanpa tercecer!")
                    st.rerun()
                else:
                    st.error("Mohon isi nama siswa dan materi terlebih dahulu.")

    with col2:
        df_sesi = ambil_semua_sesi()
        
        # --- BLOK ESTIMASI & RINGKASAN ---
        st.header("📊 Dashboard Ringkasan & Estimasi")
        if not df_sesi.empty:
            total_jam = df_sesi['durasi'].sum()
            total_tagihan = df_sesi['tagihan'].sum()
            belum_bayar = df_sesi[df_sesi['status_bayar'] == 'Belum Dibayar']['tagihan'].sum()
            
            c_jam, c_tagihan, c_belum = st.columns(3)
            c_jam.metric("Total Jam Mengajar", f"{total_jam} Jam")
            c_tagihan.metric("Total Akumulasi Tagihan", f"Rp {total_tagihan:,.0f}")
            c_belum.metric("Estimasi Belum Dibayar", f"Rp {belum_bayar:,.0f}")
            
            # --- TOMBOL UNDUH PDF ---
            st.subheader("📄 Ekspor Administrasi")
            try:
                pdf_data = generate_pdf_report(df_sesi, total_jam, total_tagihan)
                st.download_button(
                    label="📥 Unduh Laporan Riwayat & Tagihan (PDF)",
                    data=pdf_data,
                    file_name=f"Laporan_Les_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.info("Tombol PDF siap digunakan setelah library 'weasyprint' terpasang.")
        else:
            st.info("Belum ada data sesi mengajar yang terekam.")

        # --- TABEL RIWAYAT SESI ---
        st.header("📜 Riwayat Sesi Mengajar")
        if not df_sesi.empty:
            # Mempercantik tampilan dataframe di browser
            display_df = df_sesi.copy()
            st.dataframe(
                display_df[['tanggal', 'nama_siswa', 'materi', 'durasi', 'tagihan', 'status_bayar']],
                column_config={
                    "tanggal": "Tanggal & Waktu",
                    "nama_siswa": "Siswa",
                    "materi": "Materi",
                    "durasi": st.column_config.NumberColumn("Durasi", format="%.1f Jam"),
                    "tagihan": st.column_config.NumberColumn("Tagihan", format="Rp %d"),
                    "status_bayar": "Status Pembayaran"
                },
                use_container_width=True
            )
            
            # Mengubah Status Pembayaran Sesi
            st.subheader("🔄 Update Status Pembayaran")
            pilih_id = st.selectbox("Pilih ID Sesi untuk diubah:", df_sesi['id'].tolist())
            status_baru = st.radio("Status Baru:", ["Belum Dibayar", "Lunas Dibayar"], horizontal=True)
            if st.button("Perbarui Status"):
                update_status_bayar(pilih_id, status_baru)
                st.success(f"Status Sesi ID {pilih_id} berhasil diupdate!")
                st.rerun()

if __name__ == '__main__':
    main()
