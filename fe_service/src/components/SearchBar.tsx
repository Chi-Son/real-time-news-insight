import React, { useState } from "react";

type SearchBarProps = {
  onSearch: (value: string) => void;
};

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [value, setValue] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setValue(v);
    onSearch(v);
  };

  return (
    <input
      type="text"
      placeholder="Tìm kiếm chủ đề / thực thể..."
      value={value}
      onChange={handleChange}
      style={{
        width: "100%",
        padding: "10px 12px",
        borderRadius: 8,
        border: "1px solid #d1d5db",
        marginBottom: 16,
      }}
    />
  );
};

export default SearchBar;
