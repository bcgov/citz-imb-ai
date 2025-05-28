import React from "react";

import ContextProvider from "@/context/Context.tsx";

import App from "./App.tsx";
import "./index.css";
import ReactDOM from "react-dom/client";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ContextProvider>
      <App />
    </ContextProvider>
  </React.StrictMode>,
);
