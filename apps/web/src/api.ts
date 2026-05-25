export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://localhost:8000";

export type DatasetSearchResult = {
  dataset_id: string;
  title: string;
  description: string;
  agency_name: string;
  category: string;
  rows_count: number;
  source_url: string;
};

export async function runCatalogIngest(limit: number, topK: number): Promise<{
  ingest_run_id: string;
  datasets_scanned: number;
  datasets_selected: number;
  status: string;
}> {
  const url = new URL(`${API_BASE_URL}/ingest/catalog`);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("top_k", String(topK));

  const response = await fetch(url, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Ingest failed with status ${response.status}`);
  }

  return response.json();
}

export async function searchDatasets(query: string): Promise<DatasetSearchResult[]> {
  const url = new URL(`${API_BASE_URL}/datasets/search`);
  url.searchParams.set("query", query);
  url.searchParams.set("limit", "8");

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Search failed with status ${response.status}`);
  }

  const payload = (await response.json()) as { results: DatasetSearchResult[] };
  return payload.results;
}
