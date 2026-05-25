import React from "react";
import ReactDOM from "react-dom/client";
import { runCatalogIngest, searchDatasets, type DatasetSearchResult } from "./api";
import {
  EMBEDDING_MODELS,
  type EmbeddingModel,
  cosineSimilarity,
  embedText,
} from "./clientCompute";
import { listRuns, putRun } from "./localStore";
import "./styles.css";

function App() {
  const [question, setQuestion] = React.useState(
    "Which neighborhoods have rising 311 heat complaints but low tree coverage?"
  );
  const [results, setResults] = React.useState<DatasetSearchResult[]>([]);
  const [model, setModel] = React.useState<EmbeddingModel>(EMBEDDING_MODELS[0]);
  const [localComputeStatus, setLocalComputeStatus] = React.useState(
    "Waiting for local GPU compute"
  );
  const [runs, setRuns] = React.useState<
    { id: string; question: string; model: string; createdAt: string }[]
  >([]);
  const [ingestStatus, setIngestStatus] = React.useState<string>("Catalog not ingested yet");
  const [loadingIngest, setLoadingIngest] = React.useState(false);
  const [loadingSearch, setLoadingSearch] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    listRuns(5)
      .then((items) => setRuns(items))
      .catch(() => undefined);
  }, []);

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
      setLocalComputeStatus("Running WebGPU embeddings locally...");
      const queryEmbedding = await embedText(question, model);

      const found = await searchDatasets(question);

      const scored = await Promise.all(
        found.map(async (row) => {
          const datasetText = `${row.title}\n${row.description}\n${row.category}\n${row.agency_name}`;
          const rowEmbedding = await embedText(datasetText, model);
          const score = cosineSimilarity(queryEmbedding.vector, rowEmbedding.vector);
          return {
            ...row,
            local_score: score,
          };
        })
      );

      scored.sort((a, b) => b.local_score - a.local_score);
      setResults(scored);

      const runRecord = {
        id: crypto.randomUUID(),
        question,
        model,
        queryEmbeddingKey: queryEmbedding.key,
        selectedDatasetIds: scored.slice(0, 5).map((r) => r.dataset_id),
        createdAt: new Date().toISOString(),
      };
      await putRun(runRecord);
      const latestRuns = await listRuns(5);
      setRuns(latestRuns);

      setLocalComputeStatus(
        `Local compute complete (${queryEmbedding.cached ? "cache hit" : "new embedding"})`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dataset search failed");
      setLocalComputeStatus("Local compute failed");
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
          Step 1: ingest top NYC datasets. Step 2: run required local WebGPU embedding compute.
          Step 3: search and locally rerank relevant datasets.
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

        <label htmlFor="model-select">Embedding model (browser GPU)</label>
        <select
          id="model-select"
          value={model}
          onChange={(event) => setModel(event.target.value as EmbeddingModel)}
        >
          {EMBEDDING_MODELS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <div className="controls">
          <button type="button" onClick={handleSearchClick} disabled={loadingSearch}>
            {loadingSearch ? "Computing + Searching..." : "Run Local GPU Compute + Find Datasets"}
          </button>
          <span className="status">{localComputeStatus}</span>
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
              <p className="meta">Local embedding score: {(row as DatasetSearchResult & { local_score?: number }).local_score?.toFixed(4) ?? "n/a"}</p>
              <a href={row.source_url} target="_blank" rel="noreferrer">
                Open dataset API
              </a>
            </li>
          ))}
        </ul>

        <h3>Local Run History (IndexedDB)</h3>
        <ul className="result-list">
          {runs.map((run) => (
            <li key={run.id} className="result-item">
              <strong>{run.question}</strong>
              <p className="meta">
                {run.model} | {new Date(run.createdAt).toLocaleString()}
              </p>
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
