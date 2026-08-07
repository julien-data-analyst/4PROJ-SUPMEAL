// composables/usePagination.ts
interface PageResponse<T> {
  results: T[];
  total_pages: number;
}

// Walks every page of a `DefaultPagination` endpoint (capped at 100 items
// per page server-side - see backend `config.pagination.DefaultPagination`)
// and returns the concatenated results. Used wherever a UI needs the full
// set rather than a single page (e.g. patching client-side state, building
// an export selection list) instead of silently truncating at one page.
export async function fetchAllPages<T>(
  fetchPage: (page: number) => Promise<PageResponse<T>>,
): Promise<T[]> {
  const first = await fetchPage(1);
  const all = [...first.results];
  for (let page = 2; page <= first.total_pages; page++) {
    const next = await fetchPage(page);
    all.push(...next.results);
  }
  return all;
}
