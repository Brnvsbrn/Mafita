import React from "react";
import { createRoot } from "react-dom/client";
import { Agentation } from "agentation";

const isLocal =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "";

if (isLocal) {
  const rootElement = document.createElement("div");
  rootElement.id = "agentation-root";
  document.body.appendChild(rootElement);

  createRoot(rootElement).render(
    <Agentation
      onSubmit={(output) => {
        console.log("[Agentation feedback]", output);
      }}
    />
  );
}
