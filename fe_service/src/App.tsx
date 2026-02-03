import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import TopicPage from "./pages/TopicPage";
import SearchPage from "./pages/SearchPage";
import CategoryPage from "./pages/CategoryPage";
import EntityPage from "./pages/EntityPage";

const App = () => {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/topics/:topicId" element={<TopicPage />} />
      <Route path="/search" element={<SearchPage />} />
      <Route path="/category/:category" element={<CategoryPage />} />
      <Route path="/entities/:entityId" element={<EntityPage />} />
    </Routes>
  );
};

export default App;
