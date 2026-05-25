import React from "react";
import ReactDOM from "react-dom/client";
import "./styles.css";

function App() {
  return (
    <main className="app">
      <header>
        <h1>CivicGrid NYC</h1>
        <p>Ask NYC. Contribute compute. Publish reproducible insight cards.</p>
      </header>

      <section className="grid">
        <article className="card">
          <h2>Ask NYC</h2>
          <p>Natural-language civic analysis over NYC Open Data.</p>
        </article>
        <article className="card">
          <h2>Civic Compute</h2>
          <p>Simulated local workers contribute verified analysis work-units.</p>
        </article>
        <article className="card">
          <h2>Insight Atlas</h2>
          <p>Queryable, cited, and reproducible public insight cards.</p>
        </article>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
