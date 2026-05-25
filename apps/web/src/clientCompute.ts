import { env, pipeline } from "@xenova/transformers";
import { getEmbedding, putEmbedding } from "./localStore";

export const EMBEDDING_MODELS = [
  "Xenova/all-MiniLM-L6-v2",
  "Xenova/paraphrase-multilingual-MiniLM-L12-v2",
] as const;

export type EmbeddingModel = (typeof EMBEDDING_MODELS)[number];

type Extractor = (text: string, options: Record<string, unknown>) => Promise<{
  data: Float32Array | number[];
}>;

const extractorByModel = new Map<EmbeddingModel, Promise<Extractor>>();

function assertWebGPUAvailable(): void {
  if (!("gpu" in navigator)) {
    throw new Error(
      "WebGPU is required for CivicGrid zero-cloud mode. Use a WebGPU-capable browser/device."
    );
  }
}

async function hashText(input: string): Promise<string> {
  const encoded = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest("SHA-256", encoded);
  const bytes = Array.from(new Uint8Array(digest));
  return bytes.map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function getExtractor(model: EmbeddingModel): Promise<Extractor> {
  if (!extractorByModel.has(model)) {
    env.allowLocalModels = false;
    env.useBrowserCache = true;

    const extractorPromise = pipeline("feature-extraction", model, {
      device: "webgpu",
    }) as unknown as Promise<Extractor>;

    extractorByModel.set(model, extractorPromise);
  }

  return extractorByModel.get(model)!;
}

export async function embedText(text: string, model: EmbeddingModel): Promise<{
  key: string;
  vector: number[];
  cached: boolean;
}> {
  assertWebGPUAvailable();
  const normalized = text.trim().slice(0, 2400);
  if (!normalized) {
    throw new Error("Cannot embed empty text");
  }

  const key = await hashText(`${model}::${normalized}`);
  const cachedRecord = await getEmbedding(key);
  if (cachedRecord) {
    return { key, vector: cachedRecord.vector, cached: true };
  }

  const extractor = await getExtractor(model);
  const output = await extractor(normalized, { pooling: "mean", normalize: true });
  const vector = Array.from(output.data);

  await putEmbedding({
    key,
    model,
    text: normalized,
    vector,
    createdAt: new Date().toISOString(),
  });

  return { key, vector, cached: false };
}

export function cosineSimilarity(a: number[], b: number[]): number {
  const len = Math.min(a.length, b.length);
  if (len === 0) {
    return 0;
  }

  let dot = 0;
  let magA = 0;
  let magB = 0;
  for (let i = 0; i < len; i += 1) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }

  if (magA === 0 || magB === 0) {
    return 0;
  }

  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}
