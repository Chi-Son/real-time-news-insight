import React from "react";
import { theme } from "../styles/theme";

type HeaderProps = {
  keyword: string;
  setKeyword: (v: string) => void;
};

const services = [
  "Chủ đề nổi bật",
  "Thực thể nổi bật",
  "Thế giới",
  "Công nghệ",
  "Giáo dục",
];

const Header: React.FC<HeaderProps> = ({ keyword, setKeyword }) => {
  return (
    <header
      style={{
        background: theme.colors.background,
        color: theme.colors.text,
        padding: "56px 16px 40px",
        textAlign: "center",
      }}
    >
      {/* SITE NAME */}
      <h1
        style={{
          margin: 0,
          fontFamily: theme.fonts.brand,
          fontSize: 72,
          letterSpacing: 1,
        }}
      >
        VNews
      </h1>

      <p
        style={{
          marginTop: 12,
          marginBottom: 28,
          fontSize: 20,
          opacity: 0.85,
          fontFamily: theme.fonts.body,
        }}
      >
        Xu hướng tin tức hiện nay là gì?
      </p>

      {/* SEARCH */}
      <div style={{ display: "flex", justifyContent: "center" }}>
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Tìm kiếm tin tức..."
          style={{
            width: 520,
            maxWidth: "90%",
            padding: "12px 16px",
            fontSize: 16,
            fontFamily: theme.fonts.body,
            background: "transparent",
            border: "none",
            borderBottom: `1px solid ${theme.colors.text}`,
            outline: "none",
            color: theme.colors.text,
          }}
        />
      </div>

      {/* DIVIDER */}
      <div
        style={{
          height: 1,
          background: theme.colors.text,
          opacity: 0.4,
          maxWidth: 640,
          margin: "28px auto 20px",
        }}
      />

      {/* SERVICES */}
      <nav
        style={{
          display: "flex",
          justifyContent: "center",
          gap: 28,
          flexWrap: "wrap",
        }}
      >
        {services.map((service) => (
          <span
            key={service}
            style={{
              fontFamily: theme.fonts.brand,
              fontSize: 18,
              cursor: "pointer",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.textDecoration = "underline")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.textDecoration = "none")
            }
          >
            {service}
          </span>
        ))}
      </nav>
    </header>
  );
};

export default Header;
