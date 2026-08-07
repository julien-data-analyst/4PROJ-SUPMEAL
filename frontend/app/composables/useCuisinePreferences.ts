// composables/useCuisinePreferences.ts
import { useAuth } from "~/composables/useAuth";

// Frontend-only: there is no backend field for a user's preferred tags, so
// this is persisted in localStorage, keyed per account (like `useAuth`'s own
// "user" cache) so switching accounts on the same browser doesn't leak one
// user's preferences into another's.
function storageKey(userId: number): string {
  return `cuisine-preferences-${userId}`;
}

function readStored(userId: number): string[] {
  if (!import.meta.client) return [];
  try {
    const raw = localStorage.getItem(storageKey(userId));
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((t) => typeof t === "string") : [];
  } catch {
    return [];
  }
}

export function useCuisinePreferences() {
  const { user } = useAuth();
  const preferences = ref<string[]>([]);

  watch(
    () => user.value?.id,
    (userId) => {
      preferences.value = userId ? readStored(userId) : [];
    },
    { immediate: true },
  );

  const persist = () => {
    if (!import.meta.client || !user.value) return;
    localStorage.setItem(
      storageKey(user.value.id),
      JSON.stringify(preferences.value),
    );
  };

  const isPreferred = (tagName: string) =>
    preferences.value.includes(tagName.toLowerCase());

  const togglePreference = (tagName: string) => {
    const name = tagName.toLowerCase();
    preferences.value = isPreferred(name)
      ? preferences.value.filter((t) => t !== name)
      : [...preferences.value, name];
    persist();
  };

  return { preferences, isPreferred, togglePreference };
}
