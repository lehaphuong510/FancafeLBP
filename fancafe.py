import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Hệ thống Trại Hè", page_icon="🏕️", layout="centered")

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

@st.cache_data(ttl=30) # Cache data 30 giây để tránh lỗi Limit API
def load_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    # Lấy toàn bộ dữ liệu, ép kiểu SĐT thành chuỗi (text) để không mất số 0
    data = sheet.get_all_records(value_render_option='UNFORMATTED_VALUE')
    df = pd.DataFrame(data)
    # Ép kiểu rõ ràng
    if 'SDT' in df.columns:
        df['SDT'] = df['SDT'].astype(str).str.replace('.0', '', regex=False)
    return df

# Hàm clear cache khi có người nhấn nút cập nhật/checkin
def refresh_data():
    st.cache_data.clear()

# --- HÀM GHI ĐÈ LÊN GOOGLE SHEETS (CHỈ GHI Ô CẦN THIẾT) ---
def update_checkin_to_sheet(row_index_in_sheet, pic_name):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    # Cập nhật C (Đã check), D (Time), E (PIC)
    sheet.update(f"C{row_index_in_sheet}:E{row_index_in_sheet}", [[True, now, pic_name]])
    refresh_data()

def update_doorgift_to_sheet(row_index_in_sheet, pic_name):
    client = get_gspread_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    # Cập nhật F (Đã nhận), G (Time), H (PIC)
    sheet.update(f"F{row_index_in_sheet}:H{row_index_in_sheet}", [[True, now, pic_name]])
    refresh_data()

# --- CACHE QUẢN LÝ ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'staff_name' not in st.session_state:
    st.session_state['staff_name'] = ""

# --- CẤU HÌNH GIAO DIỆN & CSS (THEME XANH - VÀNG) ---
css = """
<style>
    /* Ẩn menu mặc định của Streamlit cho chuyên nghiệp */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main-title {
        color: #2e7d32; /* Xanh lá đậm */
        text-align: center; 
        font-size: 32px; 
        font-weight: bold; 
        margin-bottom: 20px;
    }
    .question-text {
        color: #fbc02d; /* Vàng nghệ */
        font-size: 18px; 
        font-weight: 600; 
        margin-bottom: 10px;
    }
    .stButton > button[kind="primary"] {
        background-color: #4caf50 !important; /* Xanh lá */
        color: white !important; 
        border: none !important;
        font-weight: bold;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #388e3c !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #fbc02d !important; /* Vàng */
        color: #333 !important;
        border: none !important;
        font-weight: bold;
    }
    /* Style cho Card thống kê */
    div[data-testid="metric-container"] {
        background-color: #e8f5e9;
        border: 2px solid #81c784;
        padding: 15px;
        border-radius: 10px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: bold;
    }
    .bg-green { background-color: #c8e6c9; color: #2e7d32; }
    .bg-red { background-color: #ffcdd2; color: #c62828; }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Hiển thị ảnh cover chung cho cả 2 màn hình (đăng nhập & app)
try:
    st.image("P web cover.jpg", use_column_width=True)
except:
    pass # Nếu không tìm thấy ảnh thì bỏ qua

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.markdown('<div class="main-title">ĐĂNG NHẬP HỆ THỐNG</div>', unsafe_allow_html=True)
    password = st.text_input("Vui lòng nhập mã truy cập của bạn:", type="password")

    danh_sach_pass_hop_le = {
        "2511": "Tú",
        "1990": "Chi",
        "1708": "Admin"
    }

    if st.button("Vào hệ thống", type="primary"):
        if password in danh_sach_pass_hop_le:
            st.session_state['staff_name'] = danh_sach_pass_hop_le[password]
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Sai password rồi nha!")

# --- MÀN HÌNH CHÍNH APP ---
else:
    # Header: Nút cập nhật & Đăng xuất
    col_hdr1, col_hdr2, col_hdr3 = st.columns([5, 3, 2])
    with col_hdr1:
        st.write(f"Đang trực: **{st.session_state['staff_name']}**")
    with col_hdr2:
        if st.button("🔄 Cập nhật Data"):
            refresh_data()
            st.toast("Đã làm mới dữ liệu!")
    with col_hdr3:
        if st.button("Đăng xuất"):
            st.session_state['logged_in'] = False
            st.session_state['staff_name'] = ""
            refresh_data()
            st.rerun()

    st.divider()
    
    # Load data
    try:
        df = load_data()
        
        # Tiền xử lý các cột True/False phòng trường hợp format khác nhau
        df['Đã check'] = df['Đã check'].astype(str).str.upper().replace({'TRUE': True, 'FALSE': False, '': False})
        df['Đã nhận gift'] = df['Đã nhận gift'].astype(str).str.upper().replace({'TRUE': True, 'FALSE': False, '': False})
        
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
        st.stop()

    # --- TẠO 2 TABS ---
    tab1, tab2 = st.tabs(["📌 TAB CHECK-IN", "🎁 TAB DOORGIFT"])

    # ----------------------------------------
    # TAB 1: CHECK-IN
    # ----------------------------------------
    with tab1:
        # 1. Thống kê (Cards)
        total_checked = len(df[df['Đã check'] == True])
        total_unchecked = len(df[df['Đã check'] == False])
        
        col_stat1, col_stat2 = st.columns(2)
        col_stat1.metric("Số Chấm. đã checkin", f"{total_checked}")
        col_stat2.metric("Số Chấm. chưa checkin", f"{total_unchecked}")
        
        # Expander Danh sách chưa checkin
        with st.expander("📝 Xem danh sách Chấm. chưa checkin"):
            df_chuacheck = df[df['Đã check'] == False][['Tên', 'SDT']]
            st.dataframe(df_chuacheck, hide_index=True, use_container_width=True)
            
        st.divider()

        # 2. Search Box
        st.markdown('<div class="question-text">Chấm. cho mình xin số điện thoại nha:</div>', unsafe_allow_html=True)
        search_checkin = st.text_input("Nhập 3 số đuôi (hoặc full số):", key="search_checkin").strip()
        
        if search_checkin:
            # Lọc những người có số điện thoại kết thúc bằng dãy số vừa nhập
            results = df[df['SDT'].astype(str).str.endswith(search_checkin)]
            
            if results.empty:
                st.warning("Không tìm thấy Chấm. nào với số điện thoại này!")
            else:
                st.success(f"Tìm thấy {len(results)} kết quả!")
                # Lặp qua các kết quả
                for idx, row in results.iterrows():
                    sheet_row = idx + 2 # Vị trí hàng thực tế trên Google Sheets (do hàng 1 là header)
                    
                    with st.container():
                        st.markdown(f"### 🧑‍💼 Tên: **{row['Tên']}**")
                        st.write(f"📞 SĐT: **{row['SDT']}**")
                        
                        if row['Đã check'] == True:
                            st.info(f"✅ Bạn này đã check in lúc {row['Time checkin']} (bởi {row['PIC 1']}).")
                        else:
                            # Nếu chưa checkin, hiện nút bấm
                            if st.button("Đã checkin", key=f"btn_chk_{sheet_row}", type="primary"):
                                with st.spinner("Đang cập nhật..."):
                                    update_checkin_to_sheet(sheet_row, st.session_state['staff_name'])
                                    st.success(f"Đã cập nhật hệ thống thành công cho {row['Tên']}!")
                                    st.rerun()
                        st.markdown("---")

    # ----------------------------------------
    # TAB 2: DOORGIFT
    # ----------------------------------------
    with tab2:
        # Lọc ra tệp NHỮNG NGƯỜI ĐÃ CHECK-IN
        df_checked_in = df[df['Đã check'] == True].copy()
        
        # 1. Tính năng: GỌI CHẤM NHẬN QUÀ (Sớm nhất)
        st.markdown('### 🎯 Phát quà theo thứ tự')
        if st.button("Gọi Chấm nhận quà", type="secondary", use_container_width=True):
            # Lọc những người chưa nhận quà
            df_chua_nhan = df_checked_in[df_checked_in['Đã nhận gift'] == False].copy()
            
            if df_chua_nhan.empty:
                st.info("Tất cả những người đã checkin đều đã nhận quà!")
            else:
                # Ép kiểu Time checkin về dạng datetime để sort chính xác
                df_chua_nhan['Time_Obj'] = pd.to_datetime(df_chua_nhan['Time checkin'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                df_chua_nhan = df_chua_nhan.sort_values(by='Time_Obj')
                
                # Lấy người đầu tiên
                earliest_person = df_chua_nhan.iloc[0]
                # Lấy lại index ban đầu trong df tổng để map ra số row trên sheet
                original_idx = earliest_person.name
                sheet_row = original_idx + 2
                
                st.success("Tén tèn ten! Xin mời bạn:")
                st.markdown(f"## 🏆 {earliest_person['Tên']}")
                st.write(f"📞 SĐT: {earliest_person['SDT']} | ⏰ Check-in lúc: {earliest_person['Time checkin']}")
                
                if st.button("Đã tặng doorgift", key=f"btn_gift_auto_{sheet_row}", type="primary"):
                    with st.spinner("Đang ghi nhận..."):
                        update_doorgift_to_sheet(sheet_row, st.session_state['staff_name'])
                        st.success("Đã ghi nhận tặng quà!")
                        st.rerun()
        
        st.divider()
        
        # 2. Tính năng: SEARCH THỦ CÔNG
        st.markdown('### 🔍 Hoặc tìm kiếm thủ công (chỉ tìm người đã checkin)')
        search_gift = st.text_input("Nhập 3 số đuôi SĐT để kiểm tra nhận quà:", key="search_gift").strip()
        
        if search_gift:
            results_gift = df_checked_in[df_checked_in['SDT'].astype(str).str.endswith(search_gift)]
            
            if results_gift.empty:
                st.warning("Không tìm thấy Chấm. này trong danh sách ĐÃ CHECK-IN!")
            else:
                for idx, row in results_gift.iterrows():
                    sheet_row = idx + 2
                    with st.container():
                        st.markdown(f"#### 🧑‍💼 **{row['Tên']}** - 📞 {row['SDT']}")
                        
                        if row['Đã nhận gift'] == True:
                            st.markdown(f'<span class="status-badge bg-red">ĐÃ LẤY QUÀ</span> (lúc {row["Time nhận gift"]})', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="status-badge bg-green">CHƯA LẤY QUÀ</span>', unsafe_allow_html=True)
                            st.write("") # Dòng trống
                            if st.button("Đã tặng doorgift", key=f"btn_gift_manual_{sheet_row}", type="primary"):
                                with st.spinner("Đang cập nhật..."):
                                    update_doorgift_to_sheet(sheet_row, st.session_state['staff_name'])
                                    st.success(f"Đã cập nhật hệ thống thành công!")
                                    st.rerun()
                        st.markdown("---")
