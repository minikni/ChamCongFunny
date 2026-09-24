import streamlit as st
import requests
from datetime import datetime
from streamlit_js_eval import get_geolocation
import math

# 1. CẤU HÌNH THÔNG TIN GRIST (Nhớ sửa ://getgrist.com và điền Key thật)
API_KEY = "f087f7a700bfe490fe00c7b5e760295d803bc022"     
DOC_ID = "tBW1Wgjnvzsj"  # Sử dụng mã ID chính xác từ file log của bạn
SERVER_URL = "https://docs.getgrist.com"

# Thiết lập giao diện Web Mobile chuyên nghiệp
st.set_page_config(page_title="Chấm Công Chuỗi Hệ Thống", layout="centered")
st.markdown("<h2 style='text-align: center; color: #0288D1;'>🕒 CHẤM CÔNG CHUỖI CỬA HÀNG</h2>", unsafe_allow_html=True)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 2. HÀM TỰ ĐỘNG TẢI DANH SÁCH CỬA HÀNG TỪ BẢNG 'SHOPS' TRÊN GRIST
@st.cache_data(ttl=10)  
def fetch_shops():
    try:
        url = f"{SERVER_URL}/api/docs/{DOC_ID}/tables/Shops/records"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            records = res.json().get("records", [])
            
            cleaned_shops = []
            for r in records:
                if "fields" in r:
                    fields = r["fields"]
                    try:
                        # ÉP KIỂU TỰ ĐỘNG: Chuyển dữ liệu vĩ độ/kinh độ từ chuỗi chữ (String) sang số thập phân (Float)
                        lat_val = float(fields.get("Latitude", 0))
                        lon_val = float(fields.get("Longitude", 0))
                        
                        cleaned_shops.append({
                            "row_id": r["id"],
                            "shop_name": fields.get("Shop_Name", "Cửa hàng không tên"),
                            "lat": lat_val,
                            "lon": lon_val
                        })
                    except (ValueError, TypeError):
                        # Bỏ qua dòng dữ liệu này nếu tọa độ bị nhập lỗi chữ/ký tự không hợp lệ
                        continue
            return cleaned_shops
    except Exception as e:
        print(f"🚨 [FETCH ERROR]: {str(e)}")
        return []
    return []

# Tải danh sách cửa hàng lên giao diện
list_shops = fetch_shops()

# Công thức tính khoảng cách vị trí (Haversine)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Mét
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

# --- GIAO DIỆN NHẬP LIỆU ---
emp_email = st.text_input("✉️ Nhập Email đăng nhập của bạn:", placeholder="vi-du: nhanvienA@gmail.com")

# Hiển thị hộp lựa chọn cơ sở thông minh (Lấy động từ bảng Shops trên Grist)
if list_shops:
    shop_options = {s["shop_name"]: s for s in list_shops}
    selected_shop_name = st.selectbox("🏬 Bạn đang làm việc tại cơ sở nào?", list(shop_options.keys()))
    selected_shop_data = shop_options[selected_shop_name]
else:
    st.error("❌ Không thể tải danh sách cửa hàng. Vui lòng cấu hình bảng 'Shops' trên Grist trước.")
    st.stop()

st.write("---")

# --- XÁC THỰC GPS DỰA TRÊN CƠ SỞ ĐƯỢC CHỌN ---
with st.spinner("🌍 Đang xác thực vị trí GPS..."):
    location = get_geolocation()

gps_valid = False
distance = 999999.0
ALLOW_DISTANCE_METER = 50.0  # Cho phép trong bán kính 50m

if location and 'coords' in location:
    user_lat = location['coords']['latitude']
    user_lon = location['coords']['longitude']
    
    # Tính khoảng cách từ nhân viên tới CHÍNH XÁC cửa hàng được chọn trên danh sách
    distance = calculate_distance(user_lat, user_lon, selected_shop_data["lat"], selected_shop_data["lon"])
    
    if distance <= ALLOW_DISTANCE_METER:
        st.success(f"✅ Hợp lệ! Bạn đang ở {selected_shop_name} (Cách: {round(distance, 1)}m)")
        gps_valid = True
    else:
        st.error(f"❌ Sai vị trí! Bạn đang cách {selected_shop_name} {round(distance, 1)}m (Tối đa {ALLOW_DISTANCE_METER}m).")
else:
    st.warning("⚠️ Vui lòng cấp quyền vị trí (GPS) trên điện thoại để mở khóa nút chấm công.")

# Hàm gửi bản ghi lên Grist
def send_to_grist(fields_data):
    url = f"{SERVER_URL}/api/docs/{DOC_ID}/tables/Timesheets/records"
    payload = {"records": [{"fields": fields_data}]}
    return requests.post(url, headers=headers, json=payload)

# --- KHU VỰC THAO TÁC ---
col1, col2 = st.columns(2)

with col1:
    if st.button("🔴 CHECK IN", use_container_width=True, type="primary", disabled=not gps_valid):
        if emp_email:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # KHỚP NỐI DỮ LIỆU: Điền Email và Số ID dòng của Cửa hàng để Grist tự kết nối mối quan hệ
            fields = {
                "Employee": emp_email, 
                "Shop": selected_shop_data["row_id"], # Gửi ID dòng (Integer) của cửa hàng
                "Clock_In": now_str,
                "Manager_Confirm": "Pending"
            }
            res = send_to_grist(fields)
            if res.status_code == 200:
                st.success("🎉 Check-in ca làm thành công!")
                st.balloons()
            else:
                st.error(f"Lỗi: {res.text}")
        else:
            st.warning("Vui lòng điền Email đăng nhập!")

with col2:
    if st.button("🟢 CHECK OUT", use_container_width=True, disabled=not gps_valid):
        if emp_email:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fields = {
                "Employee": emp_email,
                "Shop": selected_shop_data["row_id"],
                "Clock_Out": now_str,
                "Manager_Confirm": "Pending"
            }
            res = send_to_grist(fields)
            if res.status_code == 200:
                st.success("✅ Check-out ca làm thành công!")
            else:
                st.error(f"Lỗi: {res.text}")
        else:
            st.warning("Vui lòng điền Email đăng nhập!")
