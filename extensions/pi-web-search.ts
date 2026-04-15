import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Type } from "@sinclair/typebox";

// Web search and fetch tools using remote Ollama instance

interface SearchResponse {
  results: Array<{
    title: string;
    url: string;
    content: string;
  }>;
}

interface FetchResponse {
  title: string;
  content: string;
  links: string[];
}

function getOllamaHost(): string {
  return process.env.OLLAMA_HOST ?? "https://ollama.randoneering.dev";
}

function authHeaders(): Record<string, string> {
  const key = process.env.OLLAMA_API_KEY;
  return key ? { Authorization: `Bearer ${key}` } : {};
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "web_search",
    label: "Web Search",
    description: "Search the web for real-time information using the remote Ollama instance's web_search API.",
    parameters: Type.Object({
      query: Type.String({ description: "The search query to execute" }),
      max_results: Type.Optional(Type.Number({ description: "Maximum number of results to return (default: 5)", default: 5 })),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, _ctx) {
      const host = getOllamaHost();
      const response = await fetch(`${host}/api/experimental/web_search`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ query: params.query, max_results: params.max_results ?? 5 }),
        signal,
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        throw new Error(`Search API error (${response.status}): ${errorText || response.statusText}`);
      }

      const data = await response.json() as SearchResponse;
      const formatted = data.results
        .map((r, i) => `${i + 1}. ${r.title}\n   URL: ${r.url}\n   ${r.content}`)
        .join("\n\n");

      return {
        content: [{ type: "text", text: formatted || "No results found." }],
        details: { results: data.results },
      };
    },
  });

  pi.registerTool({
    name: "web_fetch",
    label: "Web Fetch",
    description: "Fetch and extract text content from a URL using the remote Ollama instance's web_fetch API.",
    parameters: Type.Object({
      url: Type.String({ description: "URL to fetch content from" }),
    }),
    async execute(_toolCallId, params, signal, _onUpdate, _ctx) {
      const host = getOllamaHost();
      const response = await fetch(`${host}/api/experimental/web_fetch`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ url: params.url }),
        signal,
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        throw new Error(`Fetch API error (${response.status}): ${errorText || response.statusText}`);
      }

      const data = await response.json() as FetchResponse;
      const formatted = [
        `Title: ${data.title}`,
        "",
        "Content:",
        data.content,
        "",
        `Links found: ${data.links?.length ?? 0}`,
        ...(data.links?.slice(0, 10).map((l) => `  - ${l}`) ?? []),
      ].join("\n");

      return {
        content: [{ type: "text", text: formatted }],
        details: { title: data.title, content: data.content, links: data.links },
      };
    },
  });
}
