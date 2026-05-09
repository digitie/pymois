import {
  Activity,
  ChevronLeft,
  ChevronRight,
  Database,
  Filter,
  MapPin,
  RefreshCcw,
  Search,
  TableProperties,
  X
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PAGE_SIZE = 50;

async function fetchJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return payload;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("ko-KR");
}

function formatDate(value) {
  if (!value) return "-";
  return value.slice(0, 10);
}

function statusLabel(value) {
  if (value === true) return "영업";
  if (value === false) return "비영업";
  return "미상";
}

function buildQuery(filters, offset) {
  const params = new URLSearchParams();
  if (filters.q.trim()) params.set("q", filters.q.trim());
  if (filters.serviceSlug) params.set("service_slug", filters.serviceSlug);
  if (filters.category) params.set("category", filters.category);
  if (filters.isOpen !== "") params.set("is_open", filters.isOpen);
  params.set("limit", String(PAGE_SIZE));
  params.set("offset", String(offset));
  return params.toString();
}

export default function App() {
  const [stats, setStats] = useState(null);
  const [services, setServices] = useState([]);
  const [places, setPlaces] = useState({ items: [], total: 0, limit: PAGE_SIZE, offset: 0 });
  const [filters, setFilters] = useState({ q: "", serviceSlug: "", category: "", isOpen: "" });
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  const categories = useMemo(
    () =>
      Array.from(new Set(services.map((service) => service.category).filter(Boolean))).sort(
        (a, b) => a.localeCompare(b, "ko")
      ),
    [services]
  );

  async function loadOverview() {
    try {
      const [statsPayload, servicesPayload] = await Promise.all([
        fetchJson("/api/stats"),
        fetchJson("/api/services")
      ]);
      setStats(statsPayload);
      setServices(servicesPayload.items || []);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadPlaces(nextOffset = offset) {
    setLoading(true);
    try {
      const query = buildQuery(filters, nextOffset);
      setPlaces(await fetchJson(`/api/places?${query}`));
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function openDetail(placeId) {
    setDetailLoading(true);
    try {
      setSelected(await fetchJson(`/api/places/${placeId}`));
      setError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    loadOverview();
  }, []);

  useEffect(() => {
    loadPlaces(0);
    setOffset(0);
  }, [filters.serviceSlug, filters.category, filters.isOpen]);

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(Math.ceil((places.total || 0) / PAGE_SIZE), 1);
  const visibleStart = places.total ? offset + 1 : 0;
  const visibleEnd = Math.min(offset + PAGE_SIZE, places.total);

  return (
    <div className="min-h-screen bg-[#eef3f7]">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-5 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded bg-brand text-white">
              <Database size={22} aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-normal text-ink">pymois DB 브라우저</h1>
              <p className="text-sm text-slate-500">mois_place_master / mois_place_detail</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              loadOverview();
              loadPlaces(offset);
            }}
            className="inline-flex h-10 items-center gap-2 rounded border border-line bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <RefreshCcw size={16} aria-hidden="true" />
            새로고침
          </button>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1500px] grid-cols-1 gap-4 px-5 py-5 xl:grid-cols-[280px_minmax(0,1fr)_420px]">
        <aside className="space-y-4">
          <section className="rounded border border-line bg-white p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
              <Filter size={16} aria-hidden="true" />
              필터
            </div>
            <form
              className="space-y-3"
              onSubmit={(event) => {
                event.preventDefault();
                setOffset(0);
                loadPlaces(0);
              }}
            >
              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">검색</span>
                <div className="flex h-10 items-center gap-2 rounded border border-line bg-white px-2">
                  <Search size={16} className="text-slate-400" aria-hidden="true" />
                  <input
                    value={filters.q}
                    onChange={(event) => setFilters({ ...filters, q: event.target.value })}
                    className="w-full border-0 bg-transparent text-sm outline-none"
                    placeholder="사업장명, 주소, 관리번호"
                  />
                </div>
              </label>

              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">분류</span>
                <select
                  value={filters.category}
                  onChange={(event) =>
                    setFilters({ ...filters, category: event.target.value, serviceSlug: "" })
                  }
                  className="h-10 w-full rounded border border-line bg-white px-2 text-sm"
                >
                  <option value="">전체</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">업종</span>
                <select
                  value={filters.serviceSlug}
                  onChange={(event) => setFilters({ ...filters, serviceSlug: event.target.value })}
                  className="h-10 w-full rounded border border-line bg-white px-2 text-sm"
                >
                  <option value="">전체</option>
                  {services
                    .filter((service) => !filters.category || service.category === filters.category)
                    .map((service) => (
                      <option key={service.serviceSlug} value={service.serviceSlug}>
                        {service.name} ({formatNumber(service.total)})
                      </option>
                    ))}
                </select>
              </label>

              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">영업 상태</span>
                <select
                  value={filters.isOpen}
                  onChange={(event) => setFilters({ ...filters, isOpen: event.target.value })}
                  className="h-10 w-full rounded border border-line bg-white px-2 text-sm"
                >
                  <option value="">전체</option>
                  <option value="true">영업</option>
                  <option value="false">비영업</option>
                </select>
              </label>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="submit"
                  className="inline-flex h-10 items-center justify-center gap-2 rounded bg-brand px-3 text-sm font-semibold text-white hover:bg-teal-800"
                >
                  <Search size={16} aria-hidden="true" />
                  검색
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setFilters({ q: "", serviceSlug: "", category: "", isOpen: "" });
                    setSelected(null);
                  }}
                  className="inline-flex h-10 items-center justify-center gap-2 rounded border border-line bg-white px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  <X size={16} aria-hidden="true" />
                  초기화
                </button>
              </div>
            </form>
          </section>

          <section className="rounded border border-line bg-white p-4 shadow-soft">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
              <Activity size={16} aria-hidden="true" />
              요약
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Stat label="전체" value={stats?.total} />
              <Stat label="영업" value={stats?.open} />
              <Stat label="좌표" value={stats?.withCoordinates} />
              <Stat label="업종" value={stats?.serviceCount} />
            </div>
          </section>
        </aside>

        <section className="min-w-0 rounded border border-line bg-white shadow-soft">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-3">
            <div className="flex items-center gap-2">
              <TableProperties size={18} className="text-brand" aria-hidden="true" />
              <div>
                <h2 className="text-base font-semibold text-ink">인허가 레코드</h2>
                <p className="text-sm text-slate-500">
                  {formatNumber(places.total)}건 · {currentPage}/{totalPages}쪽
                </p>
              </div>
            </div>
            {loading ? <span className="text-sm text-slate-500">조회 중</span> : null}
          </div>

          {error ? (
            <div className="border-b border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          ) : null}

          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] border-collapse text-left text-sm">
              <thead className="bg-panel text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-semibold">상태</th>
                  <th className="px-4 py-3 font-semibold">사업장</th>
                  <th className="px-4 py-3 font-semibold">업종</th>
                  <th className="px-4 py-3 font-semibold">주소</th>
                  <th className="px-4 py-3 font-semibold">좌표</th>
                  <th className="px-4 py-3 font-semibold">수정</th>
                </tr>
              </thead>
              <tbody>
                {places.items.map((place) => (
                  <tr
                    key={place.placeId}
                    className="border-t border-line hover:bg-teal-50/40"
                    onClick={() => openDetail(place.placeId)}
                  >
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex rounded px-2 py-1 text-xs font-semibold ${
                          place.isOpen
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {statusLabel(place.isOpen)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button className="text-left font-semibold text-ink hover:text-brand">
                        {place.placeName || "-"}
                      </button>
                      <div className="mt-1 font-mono text-xs text-slate-500">{place.mngNo}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium text-slate-800">{place.title || place.serviceSlug}</div>
                      <div className="text-xs text-slate-500">{place.serviceSlug}</div>
                    </td>
                    <td className="max-w-[360px] px-4 py-3 text-slate-700">
                      <div className="truncate">{place.roadAddress || place.lotAddress || "-"}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-600">
                      {place.lon != null && place.lat != null
                        ? `${place.lon.toFixed(6)}, ${place.lat.toFixed(6)}`
                        : "-"}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{formatDate(place.sourceModifiedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t border-line px-4 py-3">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => {
                const nextOffset = Math.max(offset - PAGE_SIZE, 0);
                setOffset(nextOffset);
                loadPlaces(nextOffset);
              }}
              className="inline-flex h-9 items-center gap-1 rounded border border-line bg-white px-3 text-sm font-medium disabled:opacity-40"
            >
              <ChevronLeft size={16} aria-hidden="true" />
              이전
            </button>
            <span className="mono-tabular text-sm text-slate-500">
              {formatNumber(visibleStart)}-{formatNumber(visibleEnd)}
            </span>
            <button
              type="button"
              disabled={offset + PAGE_SIZE >= places.total}
              onClick={() => {
                const nextOffset = offset + PAGE_SIZE;
                setOffset(nextOffset);
                loadPlaces(nextOffset);
              }}
              className="inline-flex h-9 items-center gap-1 rounded border border-line bg-white px-3 text-sm font-medium disabled:opacity-40"
            >
              다음
              <ChevronRight size={16} aria-hidden="true" />
            </button>
          </div>
        </section>

        <DetailPanel place={selected} loading={detailLoading} onClose={() => setSelected(null)} />
      </main>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded border border-line bg-panel px-3 py-2">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mono-tabular mt-1 text-lg font-semibold text-ink">{formatNumber(value)}</div>
    </div>
  );
}

function DetailPanel({ place, loading, onClose }) {
  if (!place) {
    return (
      <aside className="rounded border border-line bg-white p-5 shadow-soft">
        <div className="flex h-full min-h-[320px] items-center justify-center text-center text-sm text-slate-500">
          선택된 레코드 없음
        </div>
      </aside>
    );
  }

  const point =
    place.lon != null && place.lat != null
      ? `${place.lon.toFixed(7)}, ${place.lat.toFixed(7)}`
      : "좌표 없음";

  return (
    <aside className="rounded border border-line bg-white shadow-soft">
      <div className="flex items-start justify-between gap-3 border-b border-line p-4">
        <div>
          <div className="text-xs font-semibold uppercase text-brand">{place.serviceSlug}</div>
          <h2 className="mt-1 text-lg font-semibold text-ink">{place.placeName || "-"}</h2>
          <p className="mt-1 text-sm text-slate-500">{place.title}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="inline-flex h-9 w-9 items-center justify-center rounded border border-line hover:bg-slate-50"
          aria-label="닫기"
        >
          <X size={17} aria-hidden="true" />
        </button>
      </div>
      <div className="space-y-4 p-4">
        {loading ? <div className="text-sm text-slate-500">상세 조회 중</div> : null}
        <div className="grid grid-cols-2 gap-2">
          <Info label="상태" value={`${statusLabel(place.isOpen)} · ${place.statusName || "-"}`} />
          <Info label="인허가일" value={formatDate(place.licenseDate)} />
          <Info label="전화" value={place.telno || "-"} />
          <Info label="기관코드" value={place.opnAuthorityCode || "-"} />
        </div>

        <section>
          <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-ink">
            <MapPin size={16} className="text-brand" aria-hidden="true" />
            위치
          </h3>
          <div className="space-y-2 rounded border border-line bg-panel p-3 text-sm">
            <div>{place.roadAddress || "-"}</div>
            <div className="text-slate-500">{place.lotAddress || "-"}</div>
            <div className="font-mono text-xs text-slate-600">{point}</div>
          </div>
        </section>

        <JsonBlock title="특수 필드" data={place.detail?.specificData} />
        <JsonBlock title="정규화 데이터" data={place.detail?.recordData} />
      </div>
    </aside>
  );
}

function Info({ label, value }) {
  return (
    <div className="rounded border border-line bg-panel px-3 py-2">
      <div className="text-xs font-medium text-slate-500">{label}</div>
      <div className="mt-1 break-words text-sm font-semibold text-ink">{value}</div>
    </div>
  );
}

function JsonBlock({ title, data }) {
  return (
    <section>
      <h3 className="mb-2 text-sm font-semibold text-ink">{title}</h3>
      <pre className="max-h-64 overflow-auto rounded border border-line bg-[#111827] p-3 text-xs leading-relaxed text-slate-100">
        {JSON.stringify(data || {}, null, 2)}
      </pre>
    </section>
  );
}
