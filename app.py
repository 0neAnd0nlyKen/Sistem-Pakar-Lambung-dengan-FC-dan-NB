import streamlit as st
import pandas as pd
import math
from datetime import datetime # Import datetime here

# Import functions from nb.py and db_funcs.py
from nb import naive_bayes_diagnosis
from db_funcs import init_connection, get_table_data, get_tables, get_row_count, get_disease_details_by_code, insert_new_case_to_db

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Pakar - Database",
    page_icon="📑",
    layout="wide"
)

# Initialize session states if not already present
if 'questions' not in st.session_state:
    st.session_state.questions = [
        "Apakah Anda mual dan muntah?",
        "Apakah Anda hilang nafsu makan?",
        "Apakah Anda kesulitan menelan makanan?",
        "Apakah Anda nyeri pada tulang dada?",
        "Apakah Anda nyeri pada punggung?",
        "Apakah Anda merasakan pahit pada lidah?",
        "Apakah Anda cepat merasa kenyang?",
        "Apakah perut Anda kembung?",
        "Apakah perut terasa nyeri atau mulas?",
        "Apakah tinja Anda berwarna hitam pekat saat buang air besar?",
        "Apakah Anda mengalami gangguan pencernaan?",
        "Apakah Anda mengalami muntah darah?",
        "Apakah Anda sering bersendawa?",
        "Apakah Anda mengalami penurunan berat badan tanpa sebab?",
        "Apakah Anda kekurangan sel darah merah/Anemia?",
        "Apakah Anda mengalami keringat dingin?",
        "Apakah Anda merasa lemah?",
        "Apakah Anda perut terasa penuh?",
        "Apakah Anda tidak nyaman setelah makan?",
        "Apakah Anda merasa perih diperut bagian atas?",
        "Apakah keluar cairan dari lambung?"
    ]

# Inisialisasi jawaban jika belum ada
if 'answers' not in st.session_state:
    st.session_state.answers = [None] * len(st.session_state.questions)

# Inisialisasi step jika belum ada
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0

if 'diagnosis_complete' not in st.session_state:
    st.session_state.diagnosis_complete = False

if 'diagnosis_result' not in st.session_state:
    st.session_state.diagnosis_result = None

# Fungsi untuk menampilkan progress bar
def show_progress():
    progress = (st.session_state.current_step + 1) / len(st.session_state.questions)
    st.progress(progress)
    col1, col2 = st.columns([1, 3])
    with col1:
        st.caption(f"Pertanyaan {st.session_state.current_step + 1}/{len(st.session_state.questions)}")
    with col2:
        st.caption(f"Progress: {progress*100:.1f}%")

# Sidebar untuk navigasi
with st.sidebar:
    st.title("📊 Menu Navigasi")
    selected_menu = st.selectbox(
        "Pilih Menu:",
        ["Database", "Sistem Pakar"],
        key="menu_select"
    )

    if selected_menu == "Database":
        st.subheader("Database Operations")
        st.write("Pilih tabel dari database untuk melihat data")
    if selected_menu == "Sistem Pakar":
        st.subheader("Tahapan Diagnosis")
        st.write("1. Jawab pertanyaan gejala")
        st.write("2. Analisis dengan Naive Bayes")
        st.write("3. Hasil diagnosis")

    st.divider()

    # Tampilkan status diagnosis
    if st.session_state.diagnosis_complete:
        st.success("✅ Diagnosis Selesai")
        if st.session_state.diagnosis_result:
            st.write(f"Hasil: {st.session_state.diagnosis_result['nama_penyakit']}")
    else:
        st.info("🔍 Diagnosis Berlangsung")
        st.write(f"Pertanyaan: {st.session_state.current_step + 1}/{len(st.session_state.questions)}")

    # Tombol reset
    if st.button("🔄 Reset Diagnosis", type="secondary"):
        for key in ['answers', 'current_step', 'diagnosis_complete', 'diagnosis_result']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.caption("Sistem Pakar v1.0")


if selected_menu == "Sistem Pakar":
    # Judul halaman
    st.title("🦾 Sistem Pakar - Diagnosis Penyakit Lambung")
    st.markdown("---")

    # Tampilkan berdasarkan status
    if not st.session_state.diagnosis_complete:
        # Tampilkan pertanyaan saat ini
        if st.session_state.current_step < len(st.session_state.questions):
            st.subheader("📋 Pertanyaan Gejala")
            show_progress()

            # Tampilkan pertanyaan
            question = st.session_state.questions[st.session_state.current_step]
            st.markdown(f"### {question}")

            # Pilihan jawaban
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("✅ Ya", use_container_width=True, type="primary"):
                    st.session_state.answers[st.session_state.current_step] = 'Ya'
                    st.session_state.current_step += 1
                    st.rerun()

            with col2:
                if st.button("❌ Tidak", use_container_width=True, type="secondary"):
                    st.session_state.answers[st.session_state.current_step] = 'Tidak'
                    st.session_state.current_step += 1
                    st.rerun()

            with col3:
                # Tombol skip (opsional)
                if st.button("⏭️ Lewati", use_container_width=True):
                    st.session_state.answers[st.session_state.current_step] = 'Tidak Diketahui'
                    st.session_state.current_step += 1
                    st.rerun()

            # Tampilkan summary jawaban
            st.divider()
            with st.expander("📊 Summary Jawaban Sementara"):
                answered = sum(1 for ans in st.session_state.answers if ans is not None)
                ya_count = sum(1 for ans in st.session_state.answers if ans == 'Ya')

                col_sum1, col_sum2, col_sum3 = st.columns(3)
                with col_sum1:
                    st.metric("Total Pertanyaan", len(st.session_state.questions))
                with col_sum2:
                    st.metric("Sudah Dijawab", answered)
                with col_sum3:
                    st.metric("Gejala 'Ya'", ya_count)

                # Tampilkan jawaban sebelumnya
                if answered > 0:
                    st.write("**Jawaban terakhir:**")
                    for i, (q, a) in enumerate(zip(st.session_state.questions[:answered],
                                                  st.session_state.answers[:answered])):
                        if a:
                            st.write(f"{i+1}. {q} → **{a}**")

            # Tombol kembali
            if st.session_state.current_step > 0:
                st.divider()
                if st.button("↩️ Kembali ke Pertanyaan Sebelumnya"):
                    st.session_state.current_step -= 1
                    st.rerun()

        else:
            # Semua pertanyaan sudah dijawab, tampilkan summary dan tombol analisis
            st.success("✅ Semua pertanyaan telah dijawab!")

            st.subheader("📊 Ringkasan Jawaban Anda")

            # Hitung statistik
            ya_count = sum(1 for ans in st.session_state.answers if ans == 'Ya')
            tidak_count = sum(1 for ans in st.session_state.answers if ans == 'Tidak')
            unknown_count = sum(1 for ans in st.session_state.answers if ans == 'Tidak Diketahui')

            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            with col_stat1:
                st.metric("Total Gejala", len(st.session_state.answers))
            with col_stat2:
                st.metric("Gejala 'Ya'", ya_count)
            with col_stat3:
                st.metric("Gejala 'Tidak'", tidak_count)
            with col_stat4:
                st.metric("Tidak Diketahui", unknown_count)

            # Tampilkan detail jawaban
            with st.expander("📋 Lihat Detail Jawaban"):
                for i, (question, answer) in enumerate(zip(st.session_state.questions, st.session_state.answers)):
                    if answer == 'Ya':
                        st.markdown(f"**{i+1}. {question}** → ✅ {answer}")
                    elif answer == 'Tidak':
                        st.markdown(f"**{i+1}. {question}** → ❌ {answer}")
                    else:
                        st.markdown(f"**{i+1}. {question}** → ❓ {answer}")

            st.divider()

            # Tombol untuk memulai analisis
            st.subheader("🔬 Analisis Naive Bayes")
            st.write("Klik tombol di bawah untuk memulai analisis menggunakan algoritma Naive Bayes:")

            if st.button("🚀 Mulai Analisis", type="primary", use_container_width=True):
                with st.spinner("Menganalisis gejala menggunakan Naive Bayes..."):
                    # Panggil fungsi Naive Bayes
                    result = naive_bayes_diagnosis(st.session_state.answers)
                    if result:
                        st.session_state.diagnosis_result = result
                        st.session_state.diagnosis_complete = True
                        st.rerun()
                    else:
                        st.error("Gagal melakukan diagnosis. Silakan coba lagi.")

    else:
        # Tampilkan hasil diagnosis
        result = st.session_state.diagnosis_result

        st.success("🎉 Diagnosis Selesai!")

        # Card hasil diagnosis
        col_result1, col_result2 = st.columns([2, 1])

        with col_result1:
            st.subheader("📋 Hasil Diagnosis")
            st.markdown(f"### **{result['nama_penyakit']}**")
            st.markdown(f"**Kode Penyakit:** {result['kode_penyakit']}")

            # Confidence meter
            confidence_percent = result['confidence'] * 100
            st.metric("Tingkat Kepercayaan", f"{confidence_percent:.1f}%")

            # Progress bar untuk confidence
            st.progress(result['confidence'])

        with col_result2:
            st.metric("Gejala Terdeteksi", f"{result['gejala_terdeteksi']}/{result['total_gejala']}")
            st.metric("Status", "✅ Terdeteksi")

        st.divider()

        # Informasi penyakit (hardcoded for P01 - GERD) - This part will need to be dynamic later
        st.subheader("ℹ️ Informasi Penyakit")

        # Fetch dynamic disease details
        conn = init_connection()
        disease_details = None
        if conn:
            disease_details = get_disease_details_by_code(conn, result['kode_penyakit'])
            conn.close()

        if disease_details:
            st.markdown(f"**{disease_details['nama_penyakit']}**\n\n{disease_details['deskripsi']}")
            st.markdown("**Gejala umum:**")
            st.markdown(disease_details['gejala_umum'])
            st.markdown("**Rekomendasi:**")
            st.markdown(disease_details['rekomendasi'])
        else:
            st.info("Informasi lebih lanjut untuk penyakit ini belum tersedia.")

        st.divider()

        # Bagian rekomendasi
        st.subheader("💡 Rekomendasi")

        col_rec1, col_rec2 = st.columns(2)

        with col_rec1:
            if disease_details:
                st.markdown("**Tindakan Segera:**")
                st.markdown(disease_details['tindakan_segera'])
            else:
                st.markdown("**Tindakan Segera:**\n- Konsumsi antasida untuk meredakan gejala (jika sesuai)\n- Hindari makanan pemicu (kopi, coklat, mint, pedas, asam, berlemak)\n- Jangan merokok atau minum alkohol\n- Kelola stres dengan baik\n- Cukupi istirahat")

        with col_rec2:
            if disease_details:
                st.markdown("**Konsultasi Medis:**")
                st.markdown(disease_details['konsultasi_medis'])
            else:
                st.markdown("**Konsultasi Medis:**\n- Segera konsultasi ke dokter spesialis penyakit dalam jika gejala parah, sering kambuh, atau memburuk.\n- Dokter mungkin akan meresepkan obat atau menyarankan pemeriksaan lebih lanjut.\n- Ikuti pengobatan secara teratur dan patuhi anjuran dokter.\n- Jangan menunda pemeriksaan jika ada gejala 'red flag' seperti penurunan berat badan drastis, muntah darah, atau kesulitan menelan.")

        st.divider()

        # Tombol aksi
        col_action1, col_action2, col_action3 = st.columns(3)

        with col_action1:
            if st.button("🖨️ Cetak Hasil", use_container_width=True):
                st.success("Hasil diagnosis siap dicetak (simulasi)")

                # Simulasi data untuk cetak
                print_data = {
                    'Tanggal': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                    'Diagnosis': result['nama_penyakit'],
                    'Kode': result['kode_penyakit'],
                    'Confidence': f"{result['confidence']*100:.1f}%",
                    'Gejala Ya': result['gejala_terdeteksi'],
                    'Total Gejala': result['total_gejala']
                }

                st.json(print_data)

        with col_action2:
            if st.button("📋 Lihat Jawaban Kembali", use_container_width=True):
                st.session_state.diagnosis_complete = False
                st.session_state.current_step = len(st.session_state.questions)
                st.rerun()

        st.divider() # Add divider after the new button section to maintain layout

        if st.button("🔄 Diagnosis Baru", use_container_width=True, type="primary"):
            for key in ['answers', 'current_step', 'diagnosis_complete', 'diagnosis_result']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Footer
    st.markdown("---")
    st.caption("⚠️ **Disclaimer:** Hasil diagnosis ini hanya sebagai referensi. Silakan konsultasi dengan dokter untuk diagnosa dan pengobatan yang tepat.")
if selected_menu == "Database":
    # Judul halaman
    st.title("📑 Menu Database")
    st.markdown("---")

    # Membuat koneksi database
    connection = init_connection()

    if connection:
        if connection.is_connected():
            st.success("✅ Terhubung ke database MySQL!")

            # Dapatkan daftar tabel
            tables = get_tables(connection)

            if tables:
                # Membuat tabs untuk setiap tabel
                tabs = st.tabs([f"📋 {table}" for table in tables])

                for i, table_name in enumerate(tables):
                    with tabs[i]:
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.subheader(f"Tabel: {table_name}")

                        # Hitung jumlah baris
                        row_count = get_row_count(connection, table_name)

                        with col2:
                            st.metric("Jumlah Baris", row_count)

                        with col3:
                            if st.button("🔄 Refresh", key=f"refresh_{table_name}"):
                                st.rerun()

                        # Ambil data tabel
                        df = get_table_data(connection, table_name)

                        if not df.empty:
                            # Tampilkan dataframe
                            st.dataframe(
                                df,
                                use_container_width=True,
                                hide_index=True
                            )

                            # Tombol untuk melihat statistik
                            with st.expander("📊 Lihat Statistik"):
                                col_stat1, col_stat2, col_stat3 = st.columns(3)

                                with col_stat1:
                                    st.write("**Info Kolom:**")
                                    for col in df.columns:
                                        st.write(f"• {col}")

                                with col_stat2:
                                    st.write("**Tipe Data:**")
                                    for col in df.columns:
                                        dtype = str(df[col].dtype)
                                        st.write(f"• {dtype}")

                                with col_stat3:
                                    st.write("**Statistik:**")
                                    st.write(f"Total Baris: {len(df)}")
                                    st.write(f"Total Kolom: {len(df.columns)}")

                            # Tombol untuk ekspor data
                            col_export1, col_export2 = st.columns(2)

                            with col_export1:
                                csv = df.to_csv(index=False).encode('utf-8')
                                st.download_button(
                                    label="📥 Download CSV",
                                    data=csv,
                                    file_name=f"{table_name}.csv",
                                    mime="text/csv",
                                    key=f"csv_{table_name}"
                                )

                            with col_export2:
                                # Ekspor ke JSON
                                json_str = df.to_json(orient='records', indent=2)
                                st.download_button(
                                    label="📥 Download JSON",
                                    data=json_str,
                                    file_name=f"{table_name}.json",
                                    mime="application/json",
                                    key=f"json_{table_name}"
                                )
                        else:
                            st.warning(f"Tabel {table_name} kosong atau tidak dapat diakses.")

                        st.divider()
            else:
                st.warning("Tidak ada tabel yang ditemukan dalam database.")

            # Informasi koneksi
            with st.expander("ℹ️ Informasi Koneksi Database"):
                st.write(f"**Host:** mysql-3b8fdc2f-sistem-pakarrrrrrrrrrrr.j.aivencloud.com")
                st.write(f"**Port:** 21798")
                st.write(f"**Database:** defaultdb")
                st.write(f"**User:** avnadmin")
                st.write(f"**Status:** Terhubung")

            # Tutup koneksi saat aplikasi selesai
            if st.button("🔌 Tutup Koneksi Database"):
                connection.close()
                st.success("Koneksi database ditutup!")
                st.rerun()
        else:
            st.error("❌ Gagal terhubung ke database!")
    else:
        st.error("❌ Tidak dapat membuat koneksi ke database. Periksa kredensial Anda.")

# Footer
st.markdown("---")
st.caption("© 2024 Sistem Pakar - Menu Database")
