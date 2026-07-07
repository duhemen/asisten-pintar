# frontend/app.py
# Update bagian menu di sidebar

import streamlit as st
import requests
import json
import base64
from io import BytesIO
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Asisten Pintar Sekretaris", 
    page_icon="🏛️", 
    layout="wide"
)

# ============ SIDEBAR NAVIGASI ============
st.sidebar.title("🏛️ Asisten Pintar")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "📋 Menu Utama",
    [
        "📝 Notulensi Rapat",
        "📨 Disposisi Surat",
        "📋 TND Validator",
        "📂 Arsip Digital",  # <-- PERBAIKI INI (dari "Arsi Digital")
        "📊 Dashboard"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("v2.0.0 | Lokal & Offline")

# frontend/app.py
# ============ HALAMAN NOTULENSI ============
if menu == "📝 Notulensi Rapat":
    st.title("📝 Asisten Notulensi AI dengan Vision AI")
    st.markdown("Upload dokumen rapat untuk mendapatkan notulensi otomatis dengan AI.")
    st.markdown("---")
    
    # Upload file
    uploaded_file = st.file_uploader(
        "📤 Upload Dokumen Rapat",
        type=['pdf', 'docx', 'txt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png'],
        help="Upload file rapat dalam format PDF, Word, Excel, atau gambar"
    )
    
    # Opsi pemrosesan di sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Opsi Pemrosesan")
        processing_mode = st.radio(
            "Pilih Mode Pemrosesan:",
            [
                "🤖 Auto (Rekomendasi)",
                "👁️ Vision AI (Qwen2-VL)",
                "📄 OCR Biasa"
            ],
            index=0
        )
    
    # === INISIALISASI SESSION STATE ===
    if 'notulensi_result' not in st.session_state:
        st.session_state.notulensi_result = None
    if 'notulensi_text' not in st.session_state:
        st.session_state.notulensi_text = ""
    if 'teks_ekstraksi_notulensi' not in st.session_state:
        st.session_state.teks_ekstraksi_notulensi = ""
    
    # Tampilkan info file dan tombol proses
    if uploaded_file:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"📄 {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
        with col2:
            process_btn = st.button("🚀 Proses Notulensi", type="primary", use_container_width=True)
        
        # Proses jika tombol ditekan
        if process_btn:
            with st.status("⚙️ Memproses dokumen...", expanded=True) as status:
                status.write("📄 Membaca dan mengekstrak teks...")
                
                if processing_mode == "👁️ Vision AI (Qwen2-VL)":
                    endpoint = "http://127.0.0.1:8000/api/asisten/notulensi-dokumen-vision"
                    status.write("👁️ Menggunakan Qwen2-VL untuk ekstraksi...")
                elif processing_mode == "📄 OCR Biasa":
                    endpoint = "http://127.0.0.1:8000/api/asisten/notulensi-dokumen-ocr"
                    status.write("📄 Menggunakan OCR biasa...")
                else:
                    endpoint = "http://127.0.0.1:8000/api/asisten/notulensi-dokumen"
                    status.write("🤖 Auto-detect metode terbaik...")
                
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                
                try:
                    response = requests.post(endpoint, files=files, timeout=600)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.notulensi_result = result
                        st.session_state.notulensi_text = result.get('notulensi_ai', '')
                        st.session_state.teks_ekstraksi_notulensi = result.get('teks_ekstraksi', '')
                        status.update(label="✅ Selesai!", state="complete")
                    else:
                        error_detail = response.json().get('detail', 'Terjadi kesalahan')
                        st.error(f"❌ Error: {error_detail}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Waktu pemrosesan habis. Coba dengan file yang lebih kecil.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Tidak dapat terhubung ke backend. Pastikan server FastAPI berjalan.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # === TAMPILKAN HASIL DI LUAR STATUS ===
    result = st.session_state.notulensi_result
    notulensi = st.session_state.notulensi_text
    teks = st.session_state.teks_ekstraksi_notulensi
    
    if result and result.get('status') != 'error':
        st.markdown("---")
        
        # Tampilkan metode dan confidence
        if 'metode' in result:
            metodo = result['metode']
            icon = "🤖" if "vision" in metodo.lower() else "📄" if "ocr" in metodo.lower() else "📝"
            st.caption(f"{icon} Metode: {metodo}")
        
        if 'confidence' in result:
            conf = result['confidence'] * 100
            st.progress(conf / 100, text=f"Confidence: {conf:.0f}%")
        
        # Layout 2 kolom
        col_hasil, col_notulensi = st.columns(2, gap="large")
        
        with col_hasil:
            st.subheader("📄 Hasil Ekstraksi")
            st.text_area(
                "Isi Dokumen", 
                teks if teks else "Teks tidak ditemukan",
                height=400,
                key="ekstraksi"
            )
        
        with col_notulensi:
            st.subheader("🤖 Notulensi AI")
            if notulensi:
                st.markdown(notulensi)
            else:
                st.warning("Notulensi tidak dapat dibuat")
        
        # === TOMBOL DOWNLOAD DI LUAR STATUS ===
        st.markdown("---")
        st.subheader("📥 Download Hasil")
        
        col_d1, col_d2, col_d3 = st.columns(3)
        
        with col_d1:
            if notulensi:
                st.download_button(
                    label="📥 Download Notulensi",
                    data=notulensi,
                    file_name=f"notulensi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_notulensi_fix"
                )
        
        with col_d2:
            if teks and teks != "Teks tidak ditemukan":
                st.download_button(
                    label="📥 Download Teks Ekstraksi",
                    data=teks,
                    file_name=f"teks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_teks_fix"
                )
        
        with col_d3:
            if notulensi and teks:
                gabungan = f"""
=== TEKS EKSTRAKSI ===
{teks}

=== NOTULENSI RAPAT ===
{notulensi}

-----------------
Dihasilkan oleh Asisten Pintar
{datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
                st.download_button(
                    label="📥 Download Lengkap",
                    data=gabungan,
                    file_name=f"lengkap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_lengkap_fix"
                )
    
    elif not uploaded_file:
        st.info("📤 Upload dokumen untuk memulai notulensi")

# ============ HALAMAN DISPOSISI ============
elif menu == "📨 Disposisi Surat":
    st.title("📨 Analisis Disposisi Surat Masuk")
    st.markdown("Upload surat masuk untuk mendapatkan rekomendasi disposisi secara otomatis.")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload Surat Masuk",
            type=['pdf', 'jpg', 'jpeg', 'png', 'docx', 'txt'],
            help="Upload dokumen surat dalam format PDF, gambar, atau dokumen teks"
        )
    
    with col2:
        st.markdown("### ⚙️ Opsi")
        processing_mode = st.radio(
            "Mode Analisis:",
            ["🤖 Auto (Rekomendasi)", "👁️ Vision AI", "📄 OCR Biasa"],
            index=0
        )
        
        process_btn = st.button(
            "🔍 Analisis Disposisi", 
            type="primary", 
            use_container_width=True,
            disabled=uploaded_file is None
        )
    
    if uploaded_file:
        file_details = {
            "Filename": uploaded_file.name,
            "Size": f"{uploaded_file.size / 1024:.1f} KB",
            "Type": uploaded_file.type
        }
        st.json(file_details)
    
    # === INISIALISASI SESSION STATE ===
    if 'disposisi_data' not in st.session_state:
        st.session_state.disposisi_data = None
    if 'disposisi_teks' not in st.session_state:
        st.session_state.disposisi_teks = ""
    if 'disposisi_ringkasan' not in st.session_state:
        st.session_state.disposisi_ringkasan = ""
    if 'disposisi_kategori' not in st.session_state:
        st.session_state.disposisi_kategori = ""
    if 'disposisi_tujuan' not in st.session_state:
        st.session_state.disposisi_tujuan = ""
    if 'disposisi_urgensi' not in st.session_state:
        st.session_state.disposisi_urgensi = ""
    if 'disposisi_text_download' not in st.session_state:
        st.session_state.disposisi_text_download = ""
    
    # === PROSES ===
    if uploaded_file and process_btn:
        with st.status("⚙️ Menganalisis surat...", expanded=True) as status:
            status.write("📄 Mengekstrak teks dari dokumen...")
            
            if processing_mode == "👁️ Vision AI":
                endpoint = "http://127.0.0.1:8000/api/disposisi/dokumen?use_vision=true"
                status.write("👁️ Menggunakan Vision AI untuk ekstraksi...")
            elif processing_mode == "📄 OCR Biasa":
                endpoint = "http://127.0.0.1:8000/api/disposisi/dokumen-ocr"
                status.write("📄 Menggunakan OCR biasa...")
            else:
                endpoint = "http://127.0.0.1:8000/api/disposisi/dokumen"
                status.write("🤖 Auto-detect metode terbaik...")
            
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            progress_bar = st.progress(0, text="Memulai proses...")
            
            try:
                with requests.Session() as session:
                    response = session.post(
                        endpoint, 
                        files=files, 
                        timeout=(30, 600)
                    )
                
                progress_bar.progress(100, text="Selesai!")
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.disposisi_data = data
                    status.update(label="✅ Selesai!", state="complete")
                else:
                    try:
                        error_detail = response.json().get('detail', 'Terjadi kesalahan')
                        st.error(f"❌ Error: {error_detail}")
                    except:
                        st.error(f"❌ Error: {response.status_code} - {response.text}")
                        
            except requests.exceptions.Timeout:
                st.error("⏰ Waktu pemrosesan habis. Coba dengan file yang lebih kecil.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Tidak dapat terhubung ke backend. Pastikan server FastAPI berjalan.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
            
            finally:
                progress_bar.empty()
    
    # === TAMPILKAN HASIL DI LUAR STATUS ===
    data = st.session_state.disposisi_data
    
    if data and data.get('status') != 'error':
        st.markdown("---")
        
        if data.get('status') == 'error':
            st.error(f"❌ {data.get('message', 'Terjadi kesalahan')}")
            if data.get('teks_ekstraksi'):
                with st.expander("📄 Lihat teks ekstraksi"):
                    st.text(data['teks_ekstraksi'])
        else:
            # Ambil data dari session state
            teks = data.get('teks_ekstraksi', '')
            ringkasan = data.get('ringkasan', 'Tidak tersedia')
            kategori = data.get('kategori', 'Tidak terdeteksi')
            tujuan = data.get('rekomendasi_tujuan', 'Tidak terdeteksi')
            urgensi = data.get('urgensi', 'Biasa')
            
            # Simpan ke session state
            st.session_state.disposisi_teks = teks
            st.session_state.disposisi_ringkasan = ringkasan
            st.session_state.disposisi_kategori = kategori
            st.session_state.disposisi_tujuan = tujuan
            st.session_state.disposisi_urgensi = urgensi
            
            # Buat teks disposisi untuk download
            disposisi_text = f"""
REKOMENDASI DISPOSISI
=====================

Ringkasan: {ringkasan}

Kategori: {kategori}
Tujuan: {tujuan}
Urgensi: {urgensi}

----------
Dihasilkan oleh Asisten Pintar
{datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
            st.session_state.disposisi_text_download = disposisi_text
            
            # TAMPILKAN HASIL
            col_teks, col_disposisi = st.columns(2, gap="large")
            
            with col_teks:
                st.subheader("📄 Teks Ekstraksi")
                st.caption(f"Metode: {data.get('metode_ekstraksi', 'unknown')}")
                st.text_area(
                    "Isi Surat",
                    teks,
                    height=400,
                    key="disposisi_teks"
                )
            
            with col_disposisi:
                st.subheader("🎯 Rekomendasi Disposisi")
                
                warna_urgensi = {
                    "Segera": "🔴",
                    "Penting": "🟡",
                    "Biasa": "🟢"
                }
                
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 10px;">
                    <h4>📌 Ringkasan</h4>
                    <p style="font-size: 16px;">{ringkasan}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("📂 Kategori", value=kategori)
                with col_b:
                    st.metric("🎯 Tujuan Disposisi", value=tujuan)
                with col_c:
                    st.metric("⚡ Urgensi", value=f"{warna_urgensi.get(urgensi, '🟢')} {urgensi}")
                
                st.markdown("---")
                st.success("✅ Rekomendasi disposisi siap ditindaklanjuti")
                
                col_act1, col_act2, col_act3 = st.columns(3)
                with col_act1:
                    if st.button("📧 Kirim ke Tujuan", use_container_width=True, key="btn_kirim"):
                        st.info("🚀 Fitur integrasi email akan segera hadir!")
                with col_act2:
                    if st.button("📄 Cetak Disposisi", use_container_width=True, key="btn_cetak"):
                        st.info("🖨️ Fitur cetak akan segera hadir!")
                with col_act3:
                    if st.button("💾 Simpan Arsip", use_container_width=True, key="btn_arsip"):
                        st.success("✅ Disposisi berhasil disimpan ke arsip!")
                        st.balloons()
    
    # === TOMBOL DOWNLOAD DI LUAR STATUS ===
    if st.session_state.disposisi_data and st.session_state.disposisi_data.get('status') != 'error':
        st.markdown("---")
        st.subheader("📥 Download Hasil")
        st.caption("Klik tombol di bawah untuk mendownload hasil analisis")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            if st.session_state.disposisi_text_download:
                st.download_button(
                    label="📥 Download Disposisi",
                    data=st.session_state.disposisi_text_download,
                    file_name=f"disposisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_disposisi_fix"
                )
        
        with col_dl2:
            if st.session_state.disposisi_teks:
                st.download_button(
                    label="📥 Download Teks Ekstraksi",
                    data=st.session_state.disposisi_teks,
                    file_name=f"teks_ekstraksi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_teks_fix"
                )
        
        with col_dl3:
            if st.session_state.disposisi_text_download and st.session_state.disposisi_teks:
                gabungan = f"""
=== TEKS EKSTRAKSI ===
{st.session_state.disposisi_teks}

=== REKOMENDASI DISPOSISI ===
{st.session_state.disposisi_text_download}
"""
                st.download_button(
                    label="📥 Download Lengkap",
                    data=gabungan,
                    file_name=f"lengkap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_lengkap_fix"
                )
    
    # ============ TOMBOL DOWNLOAD DI LUAR STATUS ============
    # Hanya tampil jika ada data dan tidak error
    if data and data.get('status') != 'error' and disposisi_text:
        st.markdown("---")
        st.subheader("📥 Download Hasil")
        st.caption("Klik tombol di bawah untuk mendownload hasil analisis")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            # Download Disposisi
            st.download_button(
                label="📥 Download Disposisi",
                data=disposisi_text,
                file_name=f"disposisi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_disposisi_final"
            )
        
        with col_dl2:
            # Download Teks Ekstraksi
            if teks:
                st.download_button(
                    label="📥 Download Teks Ekstraksi",
                    data=teks,
                    file_name=f"teks_ekstraksi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="download_teks_final"
                )
        
        with col_dl3:
            # Download Gabungan (Disposisi + Teks)
            gabungan = f"""
=== TEKS EKSTRAKSI ===
{teks}

=== REKOMENDASI DISPOSISI ===
{disposisi_text}
"""
            st.download_button(
                label="📥 Download Lengkap",
                data=gabungan,
                file_name=f"lengkap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_lengkap_final"
            )
# ============ HALAMAN TND VALIDATOR ============
elif menu == "📋 TND Validator":
    st.title("📋 Validator Tata Naskah Dinas (TND)")
    st.markdown("Validasi otomatis format surat sesuai Peraturan Tata Naskah Dinas.")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload Dokumen Surat",
            type=['docx', 'pdf', 'txt'],
            help="Upload dokumen surat untuk divalidasi formatnya"
        )
    
    with col2:
        st.markdown("### 📋 Standar TND")
        try:
            standar_response = requests.get("http://127.0.0.1:8000/api/tnd/standar", timeout=2)
            if standar_response.status_code == 200:
                standar = standar_response.json().get('standar', {})
                with st.expander("📖 Lihat Standar"):
                    st.markdown(f"""
                    **Font:** {', '.join(standar.get('font', {}).get('nama', []))} ({standar.get('font', {}).get('ukuran', '12pt')})
                    
                    **Spasi:** {standar.get('font', {}).get('spasi', '1.5')}
                    
                    **Margin:** Top {standar.get('margin', {}).get('top', '4cm')}, Bottom {standar.get('margin', {}).get('bottom', '3cm')}
                    
                    **Format Nomor Surat:** `{standar.get('nomor_surat', '000/000/Instansi/Kode/Bulan/Tahun')}`
                    
                    **Contoh:** `{standar.get('contoh_nomor', '005/123/Diskominfo/A/2024')}`
                    """)
        except:
            st.warning("⚠️ Tidak dapat mengambil standar dari backend")
    
    # Tombol validasi
    if uploaded_file:
        if st.button("🔍 Validasi TND", type="primary", use_container_width=True):
            with st.status("⚙️ Memvalidasi dokumen...", expanded=True) as status:
                status.write("📄 Membaca dokumen...")
                
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                
                try:
                    response = requests.post(
                        "http://127.0.0.1:8000/api/tnd/validate",
                        files=files,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status.update(label="✅ Selesai!", state="complete")
                        
                        st.markdown("---")
                        
                        # Tampilkan hasil
                        col_result, col_detail = st.columns(2)
                        
                        with col_result:
                            st.subheader("📊 Hasil Validasi")
                            
                            # Status
                            is_valid = data.get('is_valid', False)
                            if is_valid:
                                st.success("✅ **DOKUMEN VALID**")
                                st.balloons()
                            else:
                                st.error("❌ **DOKUMEN PERLU PERBAIKAN**")
                            
                            # Ringkasan
                            col_e, col_w, col_s = st.columns(3)
                            with col_e:
                                st.metric("❌ Error", data.get('total_errors', 0))
                            with col_w:
                                st.metric("⚠️ Warning", data.get('total_warnings', 0))
                            with col_s:
                                st.metric("💡 Saran", data.get('total_suggestions', 0))
                            
                            # Tampilkan errors
                            if data.get('errors'):
                                st.markdown("#### ❌ Error:")
                                for error in data['errors']:
                                    st.error(f"• {error}")
                            
                            # Tampilkan warnings
                            if data.get('warnings'):
                                st.markdown("#### ⚠️ Warnings:")
                                for warning in data['warnings']:
                                    st.warning(f"• {warning}")
                            
                            # Tampilkan suggestions
                            if data.get('suggestions'):
                                st.markdown("#### 💡 Saran Perbaikan:")
                                for suggestion in data['suggestions']:
                                    st.info(f"• {suggestion}")
                        
                        with col_detail:
                            st.subheader("📄 Detail Dokumen")
                            
                            details = data.get('details', {})
                            
                            # Info file
                            file_info = data.get('file_info', {})
                            st.markdown(f"""
                            **Filename:** {file_info.get('filename', '-')}
                            
                            **Ukuran:** {file_info.get('size_kb', 0)} KB
                            
                            **Jumlah Kata:** {details.get('word_count', 0)}
                            
                            **Halaman:** {details.get('pages', 1)}
                            """)
                            
                            # Detail validasi
                            if details.get('nomor_surat'):
                                st.success(f"✅ Nomor Surat: `{details['nomor_surat']}`")
                            
                            if details.get('font_name'):
                                st.info(f"📝 Font: {details['font_name']}")
                            
                            if details.get('font_size'):
                                st.info(f"📏 Font Size: {details['font_size']}pt")
                            
                            if details.get('kop_surat'):
                                st.success(f"✅ Kop Surat: {', '.join(details['kop_surat'])}")
                            
                            if details.get('tanda_tangan'):
                                st.success(f"✅ Tanda Tangan: {', '.join(details['tanda_tangan'])}")
                            
                            # Tombol download
                            if data.get('details', {}).get('full_text'):
                                st.download_button(
                                    label="📥 Download Teks Hasil Validasi",
                                    data=data['details']['full_text'],
                                    file_name=f"validasi_{uploaded_file.name.split('.')[0]}.txt",
                                    mime="text/plain",
                                    use_container_width=True
                                )
                    else:
                        error = response.json().get('detail', 'Terjadi kesalahan')
                        st.error(f"❌ Error: {error}")
                        
                except requests.exceptions.Timeout:
                    st.error("⏰ Waktu validasi habis. Coba dengan file yang lebih kecil.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Tidak dapat terhubung ke backend. Pastikan server FastAPI berjalan.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    else:
        st.info("📤 Upload dokumen surat untuk memulai validasi TND")

# ============ HALAMAN ARSIP ============
elif menu == "📂 Arsip Digital":
    st.title("📂 Arsip Digital")
    st.markdown("Kelola dan cari arsip dokumen secara terpusat.")
    st.markdown("---")
    
    # Tab untuk navigasi
    tab1, tab2, tab3 = st.tabs(["📋 Daftar Arsip", "🔍 Cari Arsip", "📊 Statistik"])
    
    with tab1:
        st.subheader("📋 Daftar Arsip")
        
        # Filter
        col1, col2 = st.columns(2)
        with col1:
            klasifikasi_filter = st.selectbox(
                "Klasifikasi",
                ["Semua", "aktif", "inaktif", "statis"]
            )
        with col2:
            kategori_filter = st.selectbox(
                "Kategori",
                ["Semua", "Keuangan", "Kepegawaian", "Infrastruktur", "Protokoler", "Umum"]
            )
        
        if st.button("🔍 Tampilkan Arsip"):
            # Panggil API pencarian
            params = {}
            if klasifikasi_filter != "Semua":
                params["klasifikasi"] = klasifikasi_filter
            if kategori_filter != "Semua":
                params["kategori"] = kategori_filter
            
            try:
                response = requests.get(
                    "http://127.0.0.1:8000/api/arsip/cari",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if results:
                        for arsip in results:
                            with st.container():
                                col_a, col_b, col_c = st.columns([3, 1, 1])
                                with col_a:
                                    st.markdown(f"**📄 {arsip.get('judul', 'No Title')}**")
                                    st.caption(f"Nomor: {arsip.get('nomor_surat', '-')}")
                                with col_b:
                                    st.caption(f"📂 {arsip.get('kategori', '-')}")
                                with col_c:
                                    status_color = "🟢" if arsip.get('klasifikasi') == 'aktif' else "🟡" if arsip.get('klasifikasi') == 'inaktif' else "🔴"
                                    st.caption(f"{status_color} {arsip.get('klasifikasi', '-')}")
                                st.divider()
                    else:
                        st.info("Belum ada arsip")
                else:
                    st.error("Gagal mengambil data arsip")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("🔍 Cari Arsip")
        
        keyword = st.text_input("Kata Kunci", placeholder="Cari judul atau nomor surat...")
        
        col1, col2 = st.columns(2)
        with col1:
            tanggal_awal = st.date_input("Tanggal Awal")
        with col2:
            tanggal_akhir = st.date_input("Tanggal Akhir")
        
        if st.button("🔍 Cari", type="primary"):
            params = {}
            if keyword:
                params["keyword"] = keyword
            if tanggal_awal:
                params["tanggal_awal"] = tanggal_awal.isoformat()
            if tanggal_akhir:
                params["tanggal_akhir"] = tanggal_akhir.isoformat()
            
            try:
                response = requests.get(
                    "http://127.0.0.1:8000/api/arsip/cari",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    st.write(f"**Ditemukan {len(results)} arsip**")
                    
                    for arsip in results:
                        with st.expander(f"📄 {arsip.get('judul', 'No Title')}"):
                            st.json(arsip)
                else:
                    st.error("Gagal mencari arsip")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with tab3:
        st.subheader("📊 Statistik Arsip")
        
        try:
            stats_response = requests.get("http://127.0.0.1:8000/api/dashboard/stats", timeout=5)
            if stats_response.status_code == 200:
                stats = stats_response.json()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📁 Aktif", stats.get('arsip_aktif', 0))
                with col2:
                    st.metric("📁 Inaktif", stats.get('arsip_inaktif', 0))
                with col3:
                    st.metric("📁 Statis", stats.get('arsip_statis', 0))
                
                total = stats.get('arsip_aktif', 0) + stats.get('arsip_inaktif', 0) + stats.get('arsip_statis', 0)
                st.metric("📊 Total Arsip", total)
        except Exception as e:
            st.error(f"Gagal mengambil statistik: {e}")

# ============ HALAMAN DASHBOARD ============
# frontend/app.py
# Cari bagian Dashboard, pastikan kodenya seperti ini:

elif menu == "📊 Dashboard":
    st.title("📊 Dashboard Pimpinan")
    st.markdown("Ringkasan kinerja dan statistik surat-menyurat.")
    st.markdown("---")
    
    try:
        # Ambil data dari backend
        stats_response = requests.get("http://127.0.0.1:8000/api/dashboard/stats", timeout=5)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    label="📨 Total Dokumen",
                    value=stats.get('total_dokumen', 0),
                    delta=f"+{stats.get('dokumen_hari_ini', 0)} hari ini"
                )
            with col2:
                st.metric(
                    label="📤 Total Surat",
                    value=stats.get('total_surat', 0),
                    delta=f"+{stats.get('surat_hari_ini', 0)} hari ini"
                )
            with col3:
                st.metric(
                    label="⏳ Disposisi Proses",
                    value=stats.get('disposisi_terkirim', 0),
                    delta="Perlu tindakan"
                )
            with col4:
                st.metric(
                    label="✅ Selesai",
                    value=stats.get('disposisi_selesai', 0),
                    delta="Bulan ini"
                )
            
            # Arsip
            st.markdown("---")
            st.subheader("📂 Statistik Arsip")
            
            col5, col6, col7 = st.columns(3)
            with col5:
                st.metric("📁 Aktif", stats.get('arsip_aktif', 0))
            with col6:
                st.metric("📁 Inaktif", stats.get('arsip_inaktif', 0))
            with col7:
                st.metric("📁 Statis", stats.get('arsip_statis', 0))
            
            # Recent documents
            st.markdown("---")
            st.subheader("📄 Dokumen Terbaru")
            
            try:
                docs_response = requests.get("http://127.0.0.1:8000/api/dokumen/recent?limit=5", timeout=3)
                if docs_response.status_code == 200:
                    docs = docs_response.json()
                    if docs:
                        for doc in docs:
                            with st.container():
                                col_a, col_b = st.columns([3, 1])
                                with col_a:
                                    st.caption(f"📄 {doc.get('filename', 'Unknown')}")
                                with col_b:
                                    st.caption(f"🕐 {doc.get('created_at', '')[:10] if doc.get('created_at') else '-'}")
                                st.divider()
                    else:
                        st.info("Belum ada dokumen")
                else:
                    st.warning("Tidak dapat mengambil data dokumen terbaru")
            except Exception as e:
                st.warning(f"Error: {e}")
        else:
            st.warning("⚠️ Tidak dapat mengambil data dari backend")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Tidak dapat terhubung ke backend. Pastikan server FastAPI berjalan.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.caption("Jalankan: uvicorn app.main:app --reload")