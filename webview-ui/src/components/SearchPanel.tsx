import { useState, useEffect } from "react";
import {
  Search,
  FileText,
  FunctionSquare,
  Tag,
  Calendar,
  TrendingUp,
} from "lucide-react";
import { vscode } from "../utilities/vscodeApi";

interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  type: "function" | "file" | "feature" | "meeting";
  filePath?: string;
  tags: string[];
  similarity: number;
  timestamp: string;
}

const mockResults: SearchResult[] = [
  {
    id: "1",
    title: "Authentication Flow Implementation",
    snippet:
      "Used JWT tokens with refresh mechanism. The validateToken function checks token expiration, signature validity, and user permissions...",
    type: "function",
    filePath: "src/auth/validator.ts",
    tags: ["auth", "security", "critical"],
    similarity: 0.94,
    timestamp: "2025-12-07T10:30:00",
  },
  {
    id: "2",
    title: "OAuth Integration Notes",
    snippet:
      "Implemented OAuth 2.0 flow with PKCE. Supports Google, GitHub, and Microsoft providers. Token validation includes...",
    type: "feature",
    tags: ["auth", "oauth", "integration"],
    similarity: 0.87,
    timestamp: "2025-12-06T16:45:00",
  },
  {
    id: "3",
    title: "Security Review Meeting",
    snippet:
      "Discussed authentication vulnerabilities and mitigation strategies. Action items include implementing rate limiting and...",
    type: "meeting",
    tags: ["security", "meeting", "action-items"],
    similarity: 0.82,
    timestamp: "2025-12-05T14:00:00",
  },
];

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  const handleSearch = () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);
    vscode.postMessage("send_search_query", {
      query: query,
    });
  };

  // Handle messages from extension
  const handleMessage = (event: any) => {
    const message = event.data;

    if (message.command === "search_results") {
      setResults(message.data || []);
      setIsSearching(false);
    } else if (message.command === "search_error") {
      setError(message.data?.error || "Search failed");
      setIsSearching(false);
    }
  };

  // Setup message listener
  useEffect(() => {
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <div className="h-full flex flex-col bg-[#1e1e1e]">
      {/* Search Bar */}
      <div className="p-3 border-b border-[#3e3e42] bg-[#252526]">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#6a6a6a]" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search"
            className="w-full pl-8 pr-2 py-1.5 bg-[#3c3c3c] border border-[#3e3e42] rounded text-xs text-[#cccccc] placeholder-[#6a6a6a] focus:outline-none focus:border-[#007acc] transition-colors font-mono"
          />
        </div>

        {/* Search Info */}
        {error && (
          <div className="mt-2 text-xs text-red-400 font-mono">
            Error: {error}
          </div>
        )}
        {results.length > 0 && (
          <div className="mt-2 text-xs text-[#6a6a6a] font-mono">
            {results.length} results
          </div>
        )}
      </div>

      {/* Results List */}
      <div className="flex-1 overflow-auto">
        {results.length === 0 && !isSearching && !error && (
          <div className="flex items-center justify-center h-full text-[#6a6a6a] px-4">
            <div className="text-center">
              <Search className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-xs">Enter a query to search</p>
            </div>
          </div>
        )}

        {error && !isSearching && (
          <div className="flex items-center justify-center h-full text-red-400 px-4">
            <div className="text-center">
              <p className="text-xs">{error}</p>
            </div>
          </div>
        )}

        {isSearching && (
          <div className="flex items-center justify-center h-full text-[#6a6a6a]">
            <div className="text-center">
              <div className="w-6 h-6 border-2 border-[#007acc] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-xs">Searching...</p>
            </div>
          </div>
        )}

        <div className="p-2 space-y-2">
          {results.map((result) => (
            <SearchResultCard
              key={result.id}
              result={result}
              selected={selectedResult?.id === result.id}
              onClick={() => setSelectedResult(result)}
            />
          ))}
        </div>
      </div>

      {/* Selected Result Details - Expandable */}
      {selectedResult && (
        <div className="border-t border-[#3e3e42] bg-[#252526] p-3 max-h-64 overflow-auto">
          <div className="mb-3">
            <div className="flex items-start justify-between mb-2">
              <h3 className="text-xs text-[#ffffff] flex-1">
                {selectedResult.title}
              </h3>
              <div className="flex items-center gap-1 px-1.5 py-0.5 bg-[#1e1e1e] rounded text-[10px] text-[#4ec9b0] ml-2">
                <TrendingUp className="w-3 h-3" />
                {(selectedResult.similarity * 100).toFixed(0)}%
              </div>
            </div>

            {selectedResult.filePath && (
              <div className="flex items-center gap-1 text-[10px] text-[#6a6a6a] mb-2 font-mono truncate">
                <FileText className="w-3 h-3 flex-shrink-0" />
                <span className="truncate">{selectedResult.filePath}</span>
              </div>
            )}

            <p className="text-xs text-[#cccccc] leading-relaxed mb-2">
              {selectedResult.snippet}
            </p>

            <div className="flex flex-wrap gap-1 mb-2">
              {selectedResult.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 bg-[#1e1e1e] border border-[#3e3e42] rounded text-[10px] text-[#4ec9b0] font-mono"
                >
                  #{tag}
                </span>
              ))}
            </div>

            <div className="text-[10px] text-[#6a6a6a] mb-2">
              {new Date(selectedResult.timestamp).toLocaleString()}
            </div>
          </div>

          <button className="w-full px-3 py-1.5 text-xs bg-[#0e639c] hover:bg-[#1177bb] text-[#ffffff] rounded transition-colors">
            Open Full Note
          </button>
        </div>
      )}
    </div>
  );
}

function SearchResultCard({
  result,
  selected,
  onClick,
}: {
  result: SearchResult;
  selected: boolean;
  onClick: () => void;
}) {
  const getIcon = () => {
    switch (result.type) {
      case "function":
        return <FunctionSquare className="w-4 h-4 text-[#dcdcaa]" />;
      case "file":
        return <FileText className="w-4 h-4 text-[#519aba]" />;
      case "feature":
        return <Tag className="w-4 h-4 text-[#c586c0]" />;
      case "meeting":
        return <Calendar className="w-4 h-4 text-[#4ec9b0]" />;
    }
  };

  return (
    <button
      onClick={onClick}
      className={`
        w-full p-3 rounded border transition-colors text-left
        ${
          selected
            ? "bg-[#37373d] border-[#007acc]"
            : "bg-[#252526] border-[#3e3e42] hover:bg-[#2a2d2e]"
        }
      `}
    >
      <div className="flex items-start gap-2 mb-2">
        {getIcon()}
        <div className="flex-1 min-w-0">
          <h4 className="text-xs text-[#ffffff] truncate">{result.title}</h4>
          {result.filePath && (
            <div className="text-[10px] text-[#6a6a6a] font-mono truncate">
              {result.filePath}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 px-1.5 py-0.5 bg-[#1e1e1e] rounded text-[10px] text-[#4ec9b0]">
          <TrendingUp className="w-3 h-3" />
          {(result.similarity * 100).toFixed(0)}%
        </div>
      </div>

      <p className="text-xs text-[#cccccc] line-clamp-2 mb-2 leading-relaxed">
        {result.snippet}
      </p>

      <div className="flex flex-wrap gap-1">
        {result.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="px-1.5 py-0.5 bg-[#1e1e1e] rounded text-[10px] text-[#4ec9b0] font-mono"
          >
            #{tag}
          </span>
        ))}
        {result.tags.length > 3 && (
          <span className="px-1.5 py-0.5 text-[10px] text-[#6a6a6a]">
            +{result.tags.length - 3}
          </span>
        )}
      </div>
    </button>
  );
}
