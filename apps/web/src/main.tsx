import React from "react";
import ReactDOM from "react-dom/client";
import { runCatalogIngest, searchDatasets, type DatasetSearchResult } from "./api";
import "./styles.css";

function App() {
  const [question, setQuestion] = React.useState(
    "Which neighborhoods have rising 311 heat complaints but low tree coverage?"
  );
  const [results, setResults] = React.useState<DatasetSearchResult[]>([]);
  const [ingestStatus, setIngestStatus] = React.useState<string>("Catalog not ingested yet");
  const [loadingIngest, setLoadingIngest] = React.useState(false);
  const [loadingSearch, setLoadingSearch] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleIngestClick() {
    setError(null);
    setLoadingIngest(true);
    try {
      const summary = await runCatalogIngest(200, 100);
      setIngestStatus(
        `Run ${summary.ingest_run_id.slice(0, 8)}: scanned ${summary.datasets_scanned}, selected ${summary.datasets_selected}`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest request failed");
    } finally {
      setLoadingIngest(false);
    }
  }

  async function handleSearchClick() {
    setError(null);
    setLoadingSearch(true);
    try {
      const found = await searchDatasets(question);
      setResults(found);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dataset search failed");
    } finally {
      setLoadingSearch(false);
    }
  }

  return (
    <main className="app">
      <header>
        <h1>CivicGrid NYC</h1>
        <p>Ask NYC. Contribute compute. Publish reproducible insight cards.</p>
      </header>

      <section className="panel">
        <h2>Ask NYC (Live API)</h2>
        <p>
          Step 1: ingest top NYC datasets. Step 2: run a natural-language search over the
          catalog.
        </p>
        <div className="controls">
          <button type="button" onClick={handleIngestClick} disabled={loadingIngest}>
            {loadingIngest ? "Ingesting..." : "Ingest NYC Catalog"}
          </button>
          <span className="status">{ingestStatus}</span>
        </div>

        <label htmlFor="question-input">Question</label>
        <textarea
          id="question-input"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          rows={3}
        />
        <div className="controls">
          <button type="button" onClick={handleSearchClick} disabled={loadingSearch}>
            {loadingSearch ? "Searching..." : "Find Relevant Datasets"}
          </button>
        </div>

        {error ? <p className="error">{error}</p> : null}

        <ul className="result-list">
          {results.map((row) => (
            <li key={row.dataset_id} className="result-item">
              <h3>{row.title}</h3>
              <p>{row.description || "No description available."}</p>
              <p className="meta">
                <strong>{row.category}</strong> | {row.agency_name} | rows: {row.rows_count}
              </p>
              <a href={row.source_url} target="_blank" rel="noreferrer">
                Open dataset API
              </a>
            </li>
          ))}
        </ul>
      </section>

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
