import React from "react";
import { theme } from "../styles/theme";

const Header: React.FC = () => {
  return (
    <header
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 3fr 1fr",
        alignItems: "center",
        padding: "16px 24px",
        borderBottom: `1px solid ${theme.colors.border}`,
        background: theme.colors.background,
      }}
    >
      {/* LEFT */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ cursor: "pointer", fontSize: 20 }}>☰</div>
        <div
          style={{
            fontFamily: theme.fonts.brand,
            fontSize: 24,
            letterSpacing: 1,
          }}
        >
          VNews
        </div>
      </div>

      {/* CENTER (EMPTY - focus column) */}
      <div />

      {/* RIGHT */}
      <div style={{ textAlign: "right" }}>
        <input
          type="text"
          placeholder="Search"
          style={{
            background: "transparent",
            border: "none",
            borderBottom: `1px solid ${theme.colors.text}`,
            color: theme.colors.text,
            outline: "none",
            width: 120,
            fontFamily: theme.fonts.body,
          }}
        />
      </div>
    </header>
  );
};

export default Header;
