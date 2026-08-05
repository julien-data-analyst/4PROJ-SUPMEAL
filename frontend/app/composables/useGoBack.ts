// composables/useGoBack.ts

// Returns to the previous page in the app's own navigation history (e.g. a
// list filtered a certain way, a search, a cookbook page) instead of a
// hardcoded route. Falls back to `fallback` when there is no previous entry
// in this app's history (direct link, page reload, new tab).
export function useGoBack(fallback: string) {
  const router = useRouter();
  return () => {
    if (import.meta.client && window.history.state?.back) {
      router.back();
    } else {
      navigateTo(fallback);
    }
  };
}
