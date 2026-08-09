// composables/useRecipes.ts
import { useRecipeStore } from "~/stores/useRecipeStore";
import type { Recipe } from "~/stores/useRecipeStore";

export interface IngredientLine {
  key: string;
  ingredientId: number | null;
  name: string;
  image: string | null;
  quantity: string;
  unity: string;
  personNumbers: string;
}

export interface TagLine {
  key: string;
  tagId: number | null;
  name: string;
  type: string;
  description: string;
}

export interface StepLine {
  key: string;
  description: string;
  durationMinutes: string;
  type: string;
}

let uidCounter = 0;
export function uid(prefix = "item"): string {
  uidCounter += 1;
  return `${prefix}-${Date.now()}-${uidCounter}`;
}

export function emptyIngredientLine(defaultPersons = "4"): IngredientLine {
  return {
    key: uid("ing"),
    ingredientId: null,
    name: "",
    image: null,
    quantity: "",
    unity: "",
    personNumbers: defaultPersons,
  };
}

export function emptyTagLine(): TagLine {
  return {
    key: uid("tag"),
    tagId: null,
    name: "",
    type: "repas",
    description: "",
  };
}

export function emptyStepLine(): StepLine {
  return {
    key: uid("step"),
    description: "",
    durationMinutes: "",
    type: "prep",
  };
}

// The API stores step duration inside a "fake timestamp" field (`dury`) where
// only hours/minutes carry meaning - a fixed anchor date keeps this reversible.
const DURY_ANCHOR = "2000-01-01";

export function minutesToDury(minutes: string | number): string {
  const total = Math.max(0, Math.round(Number(minutes) || 0));
  const hh = String(Math.floor(total / 60)).padStart(2, "0");
  const mm = String(total % 60).padStart(2, "0");
  return `${DURY_ANCHOR}T${hh}:${mm}:00Z`;
}

export function duryToMinutes(dury: string): string {
  const date = new Date(dury);
  if (Number.isNaN(date.getTime())) return "";
  return String(date.getUTCHours() * 60 + date.getUTCMinutes());
}

export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

// Mirrors the backend's common.image_validation.ALLOWED_IMAGE_MIME_TYPES -
// the server independently sniffs the actual bytes, this is just the fast
// client-side check to reject the wrong type before it's ever uploaded.
export const ALLOWED_IMAGE_TYPES = ["image/png", "image/jpeg", "image/svg+xml"];

export function isAllowedImageFile(file: File): boolean {
  return ALLOWED_IMAGE_TYPES.includes(file.type);
}

export function relativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return "";
  const diffMs = Date.now() - date.getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "à l'instant";
  if (minutes < 60) return `Il y a ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Il y a ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Il y a ${days}j`;
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `Il y a ${weeks}sem`;
  const months = Math.floor(days / 30);
  if (months < 12) return `Il y a ${months} mois`;
  const years = Math.floor(days / 365);
  return `Il y a ${years} an${years > 1 ? "s" : ""}`;
}

// Sum of every step's duration (in minutes) - the recipe's total prep time.
export function sumStepMinutes(steps: { dury: string }[]): number {
  return steps.reduce(
    (total, step) => total + (Number(duryToMinutes(step.dury)) || 0),
    0,
  );
}

export function formatCookingDuration(minutes: string | number | null): string {
  if (minutes === null || minutes === undefined || minutes === "") return "";
  const total = Math.round(Number(minutes));
  if (Number.isNaN(total)) return "";
  if (total < 60) return `${total} min`;
  const hh = Math.floor(total / 60);
  const mm = total % 60;
  return mm ? `${hh}h${String(mm).padStart(2, "0")}` : `${hh}h`;
}

// Displays a number as a plain integer when it has no decimal part, or with
// a French comma separator otherwise (e.g. 4 -> "4", 2.5 -> "2,5").
export function formatNumber(value: string | number): string {
  const num = typeof value === "number" ? value : parseFloat(value);
  if (Number.isNaN(num)) return String(value);
  return Number.isInteger(num) ? String(num) : String(num).replace(".", ",");
}

// Tags are always stored/submitted lowercase (see TagsPanel.vue and
// useRecipesEditView.ts's buildPayload) to avoid case-variant duplicates in
// the shared tag catalogue - capitalize only here, for display.
export function capitalizeFirst(text: string): string {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Minimal, dependency-free markdown subset for recipe steps: headings, bold,
// italic, unordered/ordered lists, and hard line breaks (a trailing "\"
// before the newline - the convention the step editor's Tiptap/tiptap-markdown
// serializer uses for Shift+Enter, see StepEditor.vue) - escapes HTML first
// so this is safe to render with v-html.
export function renderStepMarkdown(source: string): string {
  const escaped = escapeHtml(source ?? "");
  const lines = escaped.split(/\r?\n/);
  const html: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let paragraphBuffer: string[] = [];

  const closeList = () => {
    if (listType) {
      html.push(listType === "ul" ? "</ul>" : "</ol>");
      listType = null;
    }
  };

  const flushParagraph = () => {
    if (paragraphBuffer.length) {
      html.push(
        `<p class="${paragraphClasses}">${paragraphBuffer.join("<br>")}</p>`,
      );
      paragraphBuffer = [];
    }
  };

  const inline = (text: string): string =>
    text
      .replace(/\*\*(.+?)\*\*/g, '<strong class="font-bold">$1</strong>')
      .replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');

  // Tailwind classes are baked directly into the generated markup (rather
  // than a scoped <style> block) since this HTML is injected via v-html and
  // never passes through the component's own template compilation.
  const headingClasses = "font-bold mt-2 mb-1";
  const listClasses = "pl-5 my-1 space-y-0.5";
  const paragraphClasses = "my-1";

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      flushParagraph();
      continue;
    }

    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    if (heading) {
      closeList();
      flushParagraph();
      const level = (heading[1]?.length ?? 1) + 2;
      html.push(
        `<h${level} class="${headingClasses}">${inline(heading[2] ?? "")}</h${level}>`,
      );
      continue;
    }

    const ordered = /^\d+\.\s+(.*)$/.exec(line);
    if (ordered) {
      flushParagraph();
      if (listType !== "ol") {
        closeList();
        html.push(`<ol class="${listClasses} list-decimal">`);
        listType = "ol";
      }
      html.push(`<li>${inline(ordered[1] ?? "")}</li>`);
      continue;
    }

    const bullet = /^[-*]\s+(.*)$/.exec(line);
    if (bullet) {
      flushParagraph();
      if (listType !== "ul") {
        closeList();
        html.push(`<ul class="${listClasses} list-disc">`);
        listType = "ul";
      }
      html.push(`<li>${inline(bullet[1] ?? "")}</li>`);
      continue;
    }

    closeList();
    const hardBreak = /\\$/.exec(line);
    if (hardBreak) {
      paragraphBuffer.push(inline(line.slice(0, -1).trimEnd()));
      continue;
    }
    paragraphBuffer.push(inline(line));
    flushParagraph();
  }

  closeList();
  flushParagraph();
  return html.join("");
}

// Very deliberately conservative: only explicit http(s):// and www. links -
// broad "looks like a domain" matching would false-positive on things like
// "180°C" abbreviations. Used to keep links out of recipe step instructions
// (see the validate() step of useRecipeEditForm).
const URL_PATTERN = /(https?:\/\/|www\.)\S+/i;

export function containsUrl(text: string): boolean {
  return URL_PATTERN.test(text ?? "");
}

export function recipeToIngredientLines(recipe: Recipe): IngredientLine[] {
  return recipe.ingredients.map((line) => ({
    key: uid("ing"),
    ingredientId: line.ingredient.id,
    name: line.ingredient.name,
    image: line.ingredient.image,
    quantity: line.quantity,
    unity: line.unity ?? "",
    personNumbers: String(line.person_numbers),
  }));
}

export function recipeToTagLines(recipe: Recipe): TagLine[] {
  return recipe.tags.map((tag) => ({
    key: uid("tag"),
    tagId: tag.id,
    name: tag.name,
    type: tag.type,
    description: tag.description ?? "",
  }));
}

export function recipeToStepLines(recipe: Recipe): StepLine[] {
  return [...recipe.steps]
    .sort((a, b) => a.step_number - b.step_number)
    .map((step) => ({
      key: uid("step"),
      description: step.description,
      durationMinutes: duryToMinutes(step.dury),
      type: step.type,
    }));
}

// Stable sort (ES2019+) - recipes keep their relative order within each
// favorite/non-favorite group, favorites just bubble to the top.
export function sortFavoritesFirst(recipes: Recipe[]): Recipe[] {
  return [...recipes].sort(
    (a, b) => Number(b.is_favorite) - Number(a.is_favorite),
  );
}

export function useRecipes() {
  const store = useRecipeStore();

  const fetchMyRecipes = (search = "", page = 1) =>
    store.fetchRecipes({ in_cookbook: false, name: search || undefined, page });

  const fetchRecentRecipes = async (limit = 3): Promise<void> => {
    await store.fetchRecipes({
      in_cookbook: false,
      page_size: limit,
    });
  };

  // Used by the planning recipe picker: only the caller's own personal
  // recipes are selectable there, name-filtered (icontains) as they type.
  const searchMyRecipes = (search: string, limit = 8) =>
    store.fetchRecipes({
      in_cookbook: false,
      name: search || undefined,
      page_size: limit,
    });

  const toggleFavorite = (recipe: Recipe) =>
    store.setFavorite(recipe.id, !recipe.is_favorite);

  return {
    store,
    fetchMyRecipes,
    fetchRecentRecipes,
    searchMyRecipes,
    toggleFavorite,
  };
}
