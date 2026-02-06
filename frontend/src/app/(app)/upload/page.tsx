"use client";

import { useState, useRef } from "react";
import { api } from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<{
    ingested: number;
    skipped: number;
    errors: string[];
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.uploadCSV(file);
      setResult(res);
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">CSV Data Upload</h1>

      <div className="max-w-2xl rounded-xl bg-white p-8 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Upload Property Data
        </h2>
        <p className="text-sm text-gray-500 mb-6">
          Upload a CSV file with property records. Required columns:
          address_line1, city, zip_code, county. Optional columns include
          parcel_id, property_type, year_built, roof_area_sqft, assessed_value,
          utility_zone, tree_cover_pct, owner_first_name, owner_last_name,
          owner_phone, owner_email, and more.
        </p>

        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <input
              ref={inputRef}
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-solar-50 file:text-solar-700 hover:file:bg-solar-100"
            />
          </div>

          {file && (
            <div className="flex items-center gap-3 rounded-lg bg-gray-50 p-3">
              <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <span className="text-sm text-gray-700">{file.name}</span>
              <span className="text-xs text-gray-500">
                ({(file.size / 1024).toFixed(1)} KB)
              </span>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="rounded-lg bg-solar-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-solar-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Uploading..." : "Upload & Ingest"}
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-6 space-y-3">
            <div className="rounded-lg bg-green-50 border border-green-200 p-4">
              <h3 className="font-semibold text-green-800">Upload Complete</h3>
              <div className="mt-2 grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-green-600">Ingested</span>
                  <p className="text-2xl font-bold text-green-800">{result.ingested}</p>
                </div>
                <div>
                  <span className="text-yellow-600">Skipped (duplicates)</span>
                  <p className="text-2xl font-bold text-yellow-800">{result.skipped}</p>
                </div>
                <div>
                  <span className="text-red-600">Errors</span>
                  <p className="text-2xl font-bold text-red-800">{result.errors.length}</p>
                </div>
              </div>
            </div>
            {result.errors.length > 0 && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                <h4 className="text-sm font-semibold text-red-800">Error Details</h4>
                <ul className="mt-2 space-y-1 text-xs text-red-700">
                  {result.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
