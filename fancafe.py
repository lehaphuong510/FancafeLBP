import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Check in LBP", page_icon="🌱", layout="centered")

# --- KẾT NỐI GOOGLE SHEETS TỪ SECRETS ---
SHEET_ID = "1D8wxawBJ97qLiBAd2ym9XNMcXzDd_zBy3INi3_sIom8"
TAB_NAME = "Fanlist"

@st.cache_resource
def get_gspread_client():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return gspread.authorize(creds)

def fix_phone_number(phone):
    p = str(phone).replace('.0', '').strip()
    if p and p != 'nan' and p != 'None' and not p.startswith('0'):
        return '0' + p
    elif p == 'nan' or p == 'None':
        return ''
    return p

@st.cache_data(ttl=30) 
def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    data = sheet.get_all_records(value_render_option='FORMATTED_VALUE')
    df = pd.DataFrame(data)
    df['SheetRow'] = df.index + 2 
    if 'SDT' in df.columns:
        df['SDT'] = df['SDT'].apply(fix_phone_number)
    return df

def refresh_data():
    st.cache_data.clear()

# --- HÀM GHI ĐÈ LÊN GOOGLE SHEETS ---
def update_checkin_to_sheet(row_index_in_sheet, pic_name):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
    sheet.update(f"C{row_index_in_sheet}:E{row_index_in_sheet}", [[True, now, pic_name]])
    refresh_data()

def update_doorgift_to_sheet(row_index_in_sheet, pic_name):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")
    sheet.update(f"F{row_index_in_sheet}:H{row_index_in_sheet}", [[True, now, pic_name]])
    refresh_data()

def format_time_vn(time_str):
    try:
        dt = pd.to_datetime(time_str)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except:
        return time_str

# --- CÁC HÀM CALLBACK (XỬ LÝ DỮ LIỆU & XÓA TEXT BOX) ---
def on_checkin_click(sheet_row, staff_name):
    update_checkin_to_sheet(sheet_row, staff_name)
    st.session_state['success_msg'] = "Đã cập nhật lên hệ thống thành công!"
    st.session_state['inp_search_checkin'] = "" 

def on_goi_cham_click():
    st.session_state['goi_cham_nhan_qua'] = True

def on_dong_goi_cham_click():
    st.session_state['goi_cham_nhan_qua'] = False

def on_doorgift_auto_click(sheet_row, staff_name):
    update_doorgift_to_sheet(sheet_row, staff_name)
    st.session_state['success_msg'] = "Đã cập nhật lên hệ thống thành công!"
    st.session_state['goi_cham_nhan_qua'] = False 

def on_doorgift_manual_click(sheet_row, staff_name):
    update_doorgift_to_sheet(sheet_row, staff_name)
    st.session_state['success_msg'] = "Đã cập nhật lên hệ thống thành công!"
    st.session_state['inp_search_gift'] = ""

# --- CACHE QUẢN LÝ TRẠNG THÁI ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'staff_name' not in st.session_state:
    st.session_state['staff_name'] = ""
if 'goi_cham_nhan_qua' not in st.session_state:
    st.session_state['goi_cham_nhan_qua'] = False
if 'success_msg' not in st.session_state:
    st.session_state['success_msg'] = ""
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "CHECK-IN"
if 'inp_search_checkin' not in st.session_state:
    st.session_state['inp_search_checkin'] = ""
if 'inp_search_gift' not in st.session_state:
    st.session_state['inp_search_gift'] = ""


# Xác định index của Tab đang Active để đổi sang màu Vàng bằng Python
active_idx = 1 if st.session_state.get('active_tab', 'CHECK-IN') == "CHECK-IN" else 2

# --- CSS TÙY CHỈNH ---
css = f"""
<style>
    footer {{visibility: hidden;}}
    .main-title {{ color: #2e7d32; text-align: center; font-size: 32px; font-weight: bold; margin-bottom: 20px; }}
    .question-text {{ color: #fbc02d; font-size: 18px; font-weight: 600; margin-bottom: 10px; }}
    
    /* Giao diện Card thống kê */
    .stat-container {{ display: flex; gap: 15px; margin-bottom: 25px; flex-wrap: nowrap; }}
    .stat-box {{ flex: 1; min-width: 0; background: #ffffff; padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #eeeeee; }}
    .stat-box.green-theme {{ border-top: 5px solid #4caf50; }}
    .stat-box.yellow-theme {{ border-top: 5px solid #fbc02d; }}
    .stat-number {{ font-size: 32px; font-weight: 800; line-height: 1.2; }}
    .green-theme .stat-number {{ color: #2e7d32; }}
    .yellow-theme .stat-number {{ color: #f57f17; }}
    .stat-label {{ font-size: 13px; font-weight: 600; color: #666; text-transform: uppercase; margin-top: 8px; }}

    /* Card kết quả */
    .user-card {{ background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); border-left: 8px solid #4caf50; margin-bottom: 15px; border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee; }}
    .user-card h4 {{ color: #2e7d32; margin-top: 0; margin-bottom: 8px; font-size: 22px; }}
    .user-card p {{ margin: 5px 0; font-size: 16px; color: #555; }}
    .status-badge {{ display: inline-block; padding: 5px 10px; border-radius: 20px; font-size: 13px; font-weight: bold; margin-top: 5px; }}
    .bg-green {{ background-color: #c8e6c9; color: #2e7d32; }}
    .bg-yellow {{ background-color: #fff9c4; color: #f57f17; }}

    /* =========================================
       1. MÀU SẮC NÚT & TAB VÀNG (BẰNG PYTHON INJECT)
       ========================================= */
    /* Mặc định mọi nút Hành động (Action) là Xanh lá */
    .stButton > button[kind="primary"] {{ 
        background-color: #4caf50 !important; 
        color: white !important; 
        border: none !important; 
        font-weight: bold; 
        border-radius: 8px; 
    }}
    
    /* Ép chính xác Nút Tab đang Active thành màu Vàng (Cụm cột số 2) */
    div[data-testid="stHorizontalBlock"]:nth-of-type(2) div[data-testid="column"]:nth-child({active_idx}) button {{
        background: linear-gradient(135deg, #fceabb 0%, #f8b500 100%) !important;
        color: #333 !important;
        border-bottom: 3px solid #f57f17 !important;
        box-shadow: 0 4px 6px rgba(245, 127, 23, 0.3) !important;
    }}

    /* =========================================
       2. ÉP NẰM NGANG CHUẨN XÁC KHÔNG CẦN VUỐT
       ========================================= */
    @media (max-width: 768px) {{
        /* Ép các block ngang không được rớt dòng và không cho tràn viền */
        div[data-testid="stHorizontalBlock"] {{
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: 100% !important;
            overflow: hidden !important; 
        }}
        
        /* Chia đều chỗ gian, quan trọng nhất là min-width: 0 để tự ép nhỏ */
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 0 !important;
            min-width: 0 !important; 
            padding: 0 3px !important;
        }}
        
        /* Cấu hình chữ trên nút tự động gói gọn lại */
        div[data-testid="stHorizontalBlock"] button {{
            padding: 5px 2px !important;
            font-size: 11px !important;
            white-space: normal !important;
            line-height: 1.2 !important;
            height: auto !important;
            min-height: 45px !important;
        }}
        
        /* Cấu hình text Header nhỏ lại xíu */
        div[data-testid="stHorizontalBlock"] p {{
            font-size: 12px !important;
            margin-bottom: 0 !important;
        }}
    }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Cover Image
try:
    st.image("P web cover.jpg", use_container_width=True)
except Exception:
    pass

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.markdown('<div class="main-title">ĐĂNG NHẬP HỆ THỐNG</div>', unsafe_allow_html=True)
    password = st.text_input("Vui lòng nhập mã truy cập của bạn:", type="password")

    danh_sach_pass_hop_le = {"2511": "Tú", "1990": "Chi", "1708": "Admin"}

    if st.button("Vào hệ thống", type="primary"):
        if password in danh_sach_pass_hop_le:
            st.session_state['staff_name'] = danh_sach_pass_hop_le[password]
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Sai password rồi nha!")

# --- MÀN HÌNH CHÍNH APP ---
else:
    # 1. KHỐI HEADER (Đã rút gọn chữ để điện thoại hiện vừa vặn 1 dòng)
    col_hdr1, col_hdr2, col_hdr3 = st.columns([3, 3, 3])
    with col_hdr1:
        st.write(f"Trực: **{st.session_state['staff_name']}**")
    with col_hdr2:
        if st.button("🔄 Cập nhật", type="secondary", use_container_width=True):
            refresh_data()
            st.toast("Đã làm mới dữ liệu!")
    with col_hdr3:
        if st.button("Đăng xuất", type="secondary", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['staff_name'] = ""
            refresh_data()
            st.rerun()

    st.divider()
    
    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        st.session_state['success_msg'] = ""
    
    try:
        df = load_data()
        df['Đã check'] = df['Đã check'].astype(str).str.upper().str.strip().map({'TRUE': True, 'FALSE': False}).fillna(False)
        df['Đã nhận gift'] = df['Đã nhận gift'].astype(str).str.upper().str.strip().map({'TRUE': True, 'FALSE': False}).fillna(False)
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        st.stop()

    # 2. KHỐI ĐIỀU HƯỚNG TAB (Đã rút gọn text)
    tab_col1, tab_col2 = st.columns(2)
    with tab_col1:
        if st.button("📌 CHECK-IN", type="primary" if st.session_state['active_tab'] == "CHECK-IN" else "secondary", use_container_width=True):
            st.session_state['active_tab'] = "CHECK-IN"
            st.rerun()
            
    with tab_col2:
        if st.button("🎁 DOORGIFT", type="primary" if st.session_state['active_tab'] == "DOORGIFT" else "secondary", use_container_width=True):
            st.session_state['active_tab'] = "DOORGIFT"
            st.rerun()
            
    st.write("") 

    # ----------------------------------------
    # NỘI DUNG TAB 1: CHECK-IN
    # ----------------------------------------
    if st.session_state['active_tab'] == "CHECK-IN":
        st.markdown('<div class="question-text">Chấm. cho mình xin số điện thoại nha:</div>', unsafe_allow_html=True)
        search_checkin = st.text_input("Nhập 3 số đuôi (hoặc full số):", key="inp_search_checkin").strip()
        
        if search_checkin:
            results = df[df['SDT'].str.endswith(search_checkin)]
            
            if results.empty:
                st.warning("Không tìm thấy Chấm. nào với số điện thoại này!")
            else:
                for idx, row in results.iterrows():
                    sheet_row = row['SheetRow']
                    
                    st.markdown(f"""
                    <div class="user-card">
                        <h4>Chấm. {row['Tên']}</h4>
                        <p>📞 SĐT: <b>{row['SDT']}</b></p>
                    """, unsafe_allow_html=True)
                    
                    if row['Đã check'] == True:
                        time_format = format_time_vn(row['Time checkin'])
                        st.markdown(f'<p><span class="status-badge bg-green">✅ Đã check-in lúc {time_format} (bởi {row["PIC 1"]})</span></p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.button(
                            "Check in", 
                            key=f"btn_chk_{sheet_row}", 
                            type="primary", 
                            use_container_width=True,
                            on_click=on_checkin_click,
                            args=(sheet_row, st.session_state['staff_name'])
                        )

        st.divider()

        total_checked = len(df[df['Đã check'] == True])
        total_unchecked = len(df[df['Đã check'] == False])
        
        st.markdown(f"""
        <div class="stat-container">
            <div class="stat-box green-theme">
                <div class="stat-number">{total_checked}</div>
                <div class="stat-label">Số Chấm. đã checkin</div>
            </div>
            <div class="stat-box yellow-theme">
                <div class="stat-number">{total_unchecked}</div>
                <div class="stat-label">Số Chấm. chưa checkin</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📝 Xem danh sách Chấm. chưa checkin"):
            df_chuacheck = df[df['Đã check'] == False][['Tên', 'SDT']]
            df_chuacheck['SDT'] = df_chuacheck['SDT'].astype(str)
            st.dataframe(df_chuacheck, hide_index=True, use_container_width=True)

    # ----------------------------------------
    # NỘI DUNG TAB 2: DOORGIFT
    # ----------------------------------------
    elif st.session_state['active_tab'] == "DOORGIFT":
        df_checked_in = df[df['Đã check'] == True].copy()
        
        st.markdown('### 🎯 Phát quà theo thứ tự')
        
        st.button(
            "Gọi Chấm nhận quà", 
            type="primary", 
            use_container_width=True,
            on_click=on_goi_cham_click
        )

        if st.session_state.get('goi_cham_nhan_qua', False):
            df_chua_nhan = df_checked_in[df_checked_in['Đã nhận gift'] == False].copy()
            
            if df_chua_nhan.empty:
                st.info("Tất cả những người đã checkin đều đã nhận quà!")
                st.session_state['goi_cham_nhan_qua'] = False
            else:
                df_chua_nhan['Time_Obj'] = pd.to_datetime(df_chua_nhan['Time checkin'], dayfirst=True, errors='coerce')
                df_chua_nhan = df_chua_nhan.sort_values(by='Time_Obj')
                
                earliest_person = df_chua_nhan.iloc[0]
                sheet_row = earliest_person['SheetRow']
                
                st.success("Tén tèn ten! Xin mời bạn:")
                st.markdown(f"""
                <div class="user-card" style="border-left-color: #fbc02d;">
                    <h4>🎁 Chấm. {earliest_person['Tên']}</h4>
                    <p>📞 SĐT: <b>{earliest_person['SDT']}</b></p>
                    <p>⏰ Check-in lúc: {format_time_vn(earliest_person['Time checkin'])}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button(
                        "Tặng doorgift", 
                        key=f"btn_gift_auto_{sheet_row}", 
                        type="primary", 
                        use_container_width=True,
                        on_click=on_doorgift_auto_click,
                        args=(sheet_row, st.session_state['staff_name'])
                    )
                with col_btn2:
                    st.button(
                        "Đóng", 
                        type="secondary", 
                        use_container_width=True,
                        on_click=on_dong_goi_cham_click
                    )
        
        st.divider()
        
        st.markdown('### 🔍 Tìm kiếm thủ công')
        search_gift = st.text_input("Nhập 3 số đuôi SĐT để kiểm tra nhận quà:", key="inp_search_gift").strip()
        
        if search_gift:
            results_gift = df_checked_in[df_checked_in['SDT'].str.endswith(search_gift)]
            
            if results_gift.empty:
                st.warning("Không tìm thấy Chấm. này trong danh sách ĐÃ CHECK-IN!")
            else:
                for idx, row in results_gift.iterrows():
                    sheet_row = row['SheetRow']
                    
                    st.markdown(f"""
                    <div class="user-card">
                        <h4>Chấm. {row['Tên']}</h4>
                        <p>📞 SĐT: <b>{row['SDT']}</b></p>
                    """, unsafe_allow_html=True)
                    
                    if row['Đã nhận gift'] == True:
                        time_gift = format_time_vn(row['Time nhận gift'])
                        st.markdown(f'<p><span class="status-badge bg-green">ĐÃ LẤY QUÀ lúc {time_gift}</span></p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<p><span class="status-badge bg-yellow">CHƯA LẤY QUÀ</span></p>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.button(
                            "Tặng doorgift", 
                            key=f"btn_gift_manual_{sheet_row}", 
                            type="primary", 
                            use_container_width=True,
                            on_click=on_doorgift_manual_click,
                            args=(sheet_row, st.session_state['staff_name'])
                        )
