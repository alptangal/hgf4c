import streamlit as st
import main

# Tiêu đề của ứng dụng
st.title("Ứng dụng Streamlit đầu tiên của bạn")

# Thêm một hộp nhập liệu
name = st.text_input("Nhập tên của bạn:", "")

# Thêm một thanh trượt
age = st.slider("Chọn tuổi của bạn:", 0, 100, 25)

# Hiển thị dữ liệu người dùng nhập
if st.button("Gửi"):
    st.write(f"Xin chào **{name}**, bạn {age} tuổi!")
else:
    st.write("Nhấn nút gửi để hiển thị kết quả.")

# Hiển thị biểu đồ ví dụ
import pandas as pd
import numpy as np

data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=["A", "B", "C"]
)

st.line_chart(data)
