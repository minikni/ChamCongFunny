import streamlit as st
import requests
from datetime import datetime
from streamlit_js_eval import get_geolocation
import math

# 1. CẤU HÌNH THÔNG TIN GRIST
API_KEY = "f087f7a700bfe490fe00c7b5e760295d803bc022"     
DOC_ID = "tBW1Wgjnvzsj"       
SERVER_URL = "https://getgrist.com"

# 2. CẤU HÌNH TỌA ĐỘ GPS THỰC TẾ CỦA CỬA HÀNG (Ví dụ mẫu dưới đây ở TP.HCM)
# Bạn hãy dùng Google Maps để lấy tọa độ chính xác của quán mình điền vào đây nhé
SHOP_LAT = 10.8202429  
SHOP_LON = 106.6743837  
ALLOW_DISTANCE_METER = 50.0  # Khoảng cách tối đa cho phép chấm công (50 mét)

# Hàm công thức Haversine tính khoảng cách giữa 2 điểm GPS (Trả về số mét)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000 # Bán kính Trái Đất tính bằng mét
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Thiết lập giao diện Web Mobile
st.set_page_config(page_title="Chấm Công GPS Bảo Mật", layout="centered")
st.markdown("<h2 style='text-align: center; color: #E65100;'>📍 CHẤM CÔNG XÁC THỰC VỊ TRÍ</h2>", unsafe_allow_html=True)

# LẤY TỌA ĐỘ GPS TỪ ĐIỆN THOẠI NHÂN VIÊN
with st.spinner("🌍 Đang xác thực vị trí GPS của bạn..."):
    location = get_geolocation()

gps_valid = False
distance = 999999.0

if location and 'coords' in location:
    user_lat = location['coords']['latitude']
    user_lon = location['coords']['longitude']
    
    # Tính khoảng cách từ nhân viên tới quán
    distance = calculate_distance(user_lat, user_lon, SHOP_LAT, SHOP_LON)
    
    if distance <= ALLOW_DISTANCE_METER:
        st.success(f"✅ Vị trí hợp lệ! Bạn đang ở trong khu vực cửa hàng (Cách: {round(distance, 1)}m)")
        gps_valid = True
    else:
        st.error(f"❌ Vị trí không hợp lệ! Bạn đang ở cách cửa hàng {round(distance, 1)}m. Khoảng cách cho phép tối đa là {ALLOW_DISTANCE_METER}m.")
else:
    st.warning("⚠️ Điện thoại của bạn chưa bật GPS hoặc chưa cấp quyền truy cập vị trí cho trình duyệt. Vui lòng cho phép truy cập vị trí để bấm chấm công.")

# Giao diện nhập thông tin
emp_name = st.text_input("👤 Họ và Tên Nhân Viên:")
emp_email = st.text_input("✉️ Email Đăng Nhập:")

st.write("---")

# Hàm gửi API lên Grist
def send_to_grist(data_records):
    # Đường dẫn chuẩn phải là: SERVER_URL + "/api/docs/" + DOC_ID + "/tables/Timesheets/records"
    url = f"{SERVER_URL}/api/docs/{DOC_ID}/tables/Timesheets/records"
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Grist bắt buộc gói tin phải nằm trong danh mục mảng 'records' chứa các 'fields'
    payload = {
        "records": [
            {
                "fields": data_records
            }
        ]
    }
    
    # Thực hiện gửi lệnh POST lên đám mây hệ thống
    response = requests.post(url, headers=headers, json=payload)
    return response
col1, col2 = st.columns(2)

# Khóa hoặc mở nút bấm dựa trên biến kiểm tra gps_valid
with col1:
    if st.button("🔴 BẮM CHECK-IN", use_container_width=True, type="primary", disabled=not gps_valid):
        if emp_name and emp_email:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fields = {
                "Employee_Name": emp_name,
                "Email": emp_email,
                "Clock_In": now_str,
                "Manager_Confirm": f"Pending (GPS OK - {round(distance,1)}m)"
            }
            res = send_to_grist(fields)
            if res.status_code == 200:
                st.success("🎉 Check-in thành công!")
                st.balloons()
            else:
                st.error(f"Lỗi: {res.text}")
        else:
            st.warning("Vui lòng điền đủ thông tin!")

with col2:
    if st.button("🟢 BẮM CHECK-OUT", use_container_width=True, disabled=not gps_valid):
        if emp_name and emp_email:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fields = {
                "Employee_Name": emp_name,
                "Email": emp_email,
                "Clock_Out": now_str,
                "Manager_Confirm": f"Pending (GPS OK - {round(distance,1)}m)"
            }
            res = send_to_grist(fields)
            if res.status_code == 200:
                st.success("✅ Check-out thành công!")
            else:
                st.error(f"Lỗi: {res.text}")
        else:
            st.warning("Vui lòng điền đủ thông tin!")
