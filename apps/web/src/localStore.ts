type EmbeddingRecord = {
  key: string;
  model: string;
  text: string;
  vector: number[];
  createdAt: string;
};

type RunRecord = {
  id: string;
  question: string;
  model: string;
  queryEmbeddingKey: string;
  selectedDatasetIds: string[];
  createdAt: string;
};

const DB_NAME = "civicgrid-local";
const DB_VERSION = 1;
const EMBEDDINGS_STORE = "embeddings";
const RUNS_STORE = "runs";

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(EMBEDDINGS_STORE)) {
        db.createObjectStore(EMBEDDINGS_STORE, { keyPath: "key" });
      }
      if (!db.objectStoreNames.contains(RUNS_STORE)) {
        db.createObjectStore(RUNS_STORE, { keyPath: "id" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error("IndexedDB open failed"));
  });
}

export async function getEmbedding(key: string): Promise<EmbeddingRecord | null> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(EMBEDDINGS_STORE, "readonly");
    const store = tx.objectStore(EMBEDDINGS_STORE);
    const req = store.get(key);

    req.onsuccess = () => resolve((req.result as EmbeddingRecord | undefined) ?? null);
    req.onerror = () => reject(req.error || new Error("Read embedding failed"));
  });
}

export async function putEmbedding(record: EmbeddingRecord): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(EMBEDDINGS_STORE, "readwrite");
    const store = tx.objectStore(EMBEDDINGS_STORE);
    const req = store.put(record);

    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error || new Error("Write embedding failed"));
  });
}

export async function putRun(record: RunRecord): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(RUNS_STORE, "readwrite");
    const store = tx.objectStore(RUNS_STORE);
    const req = store.put(record);

    req.onsuccess = () => resolve();
    req.onerror = () => reject(req.error || new Error("Write run record failed"));
  });
}

export async function listRuns(limit = 10): Promise<RunRecord[]> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(RUNS_STORE, "readonly");
    const store = tx.objectStore(RUNS_STORE);
    const req = store.getAll();

    req.onsuccess = () => {
      const all = (req.result as RunRecord[]).sort((a, b) =>
        a.createdAt < b.createdAt ? 1 : -1
      );
      resolve(all.slice(0, limit));
    };
    req.onerror = () => reject(req.error || new Error("List run records failed"));
  });
}
