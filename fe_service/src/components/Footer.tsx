import React from "react";
import { theme } from "../styles/theme";

const Footer: React.FC = () => {
    return (
        <footer
            style={{
                background: "#2c3e50",
                color: "#ecf0f1",
                padding: "60px 20px 40px",
                marginTop: "80px",
                fontFamily: theme.fonts.body,
            }}
        >
            <div
                style={{
                    maxWidth: "1400px",
                    margin: "0 auto",
                }}
            >
                <div
                    style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(3, 1fr)",
                        gap: "60px",
                        marginBottom: "40px",
                    }}
                >
                    {/* About Section */}
                    <div>
                        <h3
                            style={{
                                fontSize: "18px",
                                fontWeight: 700,
                                marginBottom: "20px",
                                marginTop: 0,
                            }}
                        >
                            Về trang web
                        </h3>
                        <p
                            style={{
                                fontSize: "14px",
                                lineHeight: "1.8",
                                opacity: 0.9,
                                margin: 0,
                            }}
                        >
                            Trang web tôi là thư viện lưu trữ và cập nhật tin tức và các chủ đề nóng hổi cùng cảm xúc bài báo.
                            Chúng tôi cam kết mang lại trải nghiệm đọc báo tốt nhất cho đọc giả.
                        </p>
                    </div>

                    {/* Contact Section */}
                    <div>
                        <h3
                            style={{
                                fontSize: "18px",
                                fontWeight: 700,
                                marginBottom: "20px",
                                marginTop: 0,
                            }}
                        >
                            Thông tin liên hệ
                        </h3>
                        <div style={{ fontSize: "14px", lineHeight: "2", opacity: 0.9 }}>
                            <p style={{ margin: "0 0 8px 0" }}>
                                Địa chỉ: Số 123, Đường ABC, Thành phố XYZ
                            </p>
                            <p style={{ margin: "0 0 8px 0" }}>
                                Email: caosychison03@gmail.com
                            </p>
                            <p style={{ margin: "0" }}>Điện thoại: 083730XXX</p>
                        </div>
                    </div>

                    {/* Policy Section */}
                    <div>
                        <h3
                            style={{
                                fontSize: "18px",
                                fontWeight: 700,
                                marginBottom: "20px",
                                marginTop: 0,
                            }}
                        >
                            Chính sách
                        </h3>
                        <div style={{ fontSize: "14px", lineHeight: "2", opacity: 0.9 }}>
                            <p style={{ margin: "0 0 8px 0" }}>Chính sách bảo mật</p>
                            <p style={{ margin: "0 0 8px 0" }}>Chính sách người dùng</p>
                            <p style={{ margin: "0" }}>Điều khoản sử dụng</p>
                        </div>
                    </div>
                </div>

                {/* Copyright */}
                <div
                    style={{
                        textAlign: "center",
                        paddingTop: "30px",
                        borderTop: "1px solid rgba(236, 240, 241, 0.2)",
                    }}
                >
                    <p
                        style={{
                            fontSize: "14px",
                            margin: "0 0 16px 0",
                            opacity: 0.8,
                        }}
                    >
                        © 2026 Bản quyền.
                    </p>
                    <p
                        style={{
                            fontSize: "14px",
                            lineHeight: "1.8",
                            opacity: 0.7,
                            margin: 0,
                            fontStyle: "italic",
                        }}
                    >
                        Trang web được sử dụng tin tức từ nhiều nguồn báo Việt chính thống.
                        Hệ thống được phát triển mang mục đích học tập cá nhân, phi thương mại.
                        Mọi quyền sở hữu trí tuệ về các tác giả tương ứng.
                        Nếu có bất kỳ vi phạm nào, vui lòng liên hệ để kịp thời xử lý.
                    </p>
                </div>
            </div>

            <style>{`
        @media (max-width: 768px) {
          footer > div > div:first-child {
            grid-template-columns: 1fr;
            gap: 40px;
          }
        }
      `}</style>
        </footer>
    );
};

export default Footer;
