import React from "react";
import { useNavigate } from "react-router-dom";
import { theme } from "../styles/theme";

type HeaderProps = {
  keyword: string;
  setKeyword: (v: string) => void;
};

const services = [
  { label: "Trang chủ", path: "/" },
  { label: "Thế giới", path: "/category/foreign" },
  { label: "Công nghệ", path: "/category/technology" },
  { label: "Giáo dục", path: "/category/education" },
  { label: "Kinh doanh", path: "/category/business" },
];

const Header: React.FC<HeaderProps> = ({ keyword, setKeyword }) => {
  const navigate = useNavigate();

  const onSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && keyword.trim()) {
      navigate(`/search?q=${encodeURIComponent(keyword.trim())}`);
    }
  };

  return (
    <header
      style={{
        background: `linear-gradient(135deg, ${theme.colors.background} 0%, #faf8f3 100%)`,
        color: theme.colors.text,
        padding: "32px 20px 28px",
        borderBottom: `3px solid ${theme.colors.text}`,
        boxShadow: "0 4px 20px rgba(0,0,0,0.08)",
        position: "relative",
      }}
    >
      <div
        style={{
          maxWidth: "1400px",
          margin: "0 auto",
          textAlign: "center",
        }}
      >
        <h1
          onClick={() => navigate("/")}
          style={{
            margin: 0,
            fontFamily: theme.fonts.brand,
            fontSize: "48px",
            fontWeight: 800,
            letterSpacing: "-1.5px",
            cursor: "pointer",
            transition: "transform 0.3s ease, opacity 0.3s ease",
            display: "inline-block",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.05)";
            e.currentTarget.style.opacity = "0.85";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
            e.currentTarget.style.opacity = "1";
          }}
        >
          VNews
        </h1>

        <p
          style={{
            margin: "10px 0 24px",
            fontSize: "16px",
            opacity: 0.75,
            fontWeight: 500,
            letterSpacing: "0.3px",
          }}
        >
          Xu hướng hiện tại là gì?
        </p>

        {/* SEARCH */}
        <div style={{ position: "relative", display: "inline-block", width: "100%", maxWidth: "650px" }}>
          <input
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={onSearch}
            placeholder="Tìm kiếm chủ đề, thực thể nổi bật, ..."
            style={{
              width: "100%",
              padding: "16px 24px",
              fontSize: "16px",
              border: `2px solid ${theme.colors.text}`,
              borderRadius: "12px",
              background: "rgba(255,255,255,0.7)",
              color: theme.colors.text,
              outline: "none",
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              boxSizing: "border-box",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}
            onFocus={(e) => {
              e.currentTarget.style.background = "white";
              e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.12)";
              e.currentTarget.style.transform = "translateY(-2px)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.7)";
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.05)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          />
          <span
            style={{
              position: "absolute",
              right: "24px",
              top: "50%",
              transform: "translateY(-50%)",
              fontSize: "20px",
              opacity: 0.4,
              pointerEvents: "none",
            }}
          >
            🔍
          </span>
        </div>

        {/* SERVICES */}
        <nav
          style={{
            marginTop: "24px",
            display: "flex",
            justifyContent: "center",
            gap: "12px",
            flexWrap: "wrap",
            paddingTop: "20px",
            borderTop: `1px solid rgba(0,0,0,0.12)`,
          }}
        >
          {services.map((s) => (
            <span
              key={s.label}
              onClick={() => navigate(s.path)}
              style={{
                fontWeight: 600,
                cursor: "pointer",
                fontSize: "14px",
                opacity: 0.8,
                padding: "8px 16px",
                borderRadius: "8px",
                transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
                border: "2px solid transparent",
                background: "rgba(255,255,255,0.4)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.9)";
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.transform = "translateY(-2px)";
                e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
                e.currentTarget.style.borderColor = theme.colors.text;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.4)";
                e.currentTarget.style.opacity = "0.8";
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
                e.currentTarget.style.borderColor = "transparent";
              }}
            >
              {s.label}
            </span>
          ))}
        </nav>
      </div>
    </header>
  );
};

export default Header;
