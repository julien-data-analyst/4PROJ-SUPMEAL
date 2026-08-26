<script setup lang="ts">
import { useApi } from "~/composables/useAPI";
import { relativeTime } from "~/composables/useRecipes";
import { useAuth } from "~/composables/useAuth";
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import { useToastStore } from "~/stores/useToastStore";
import {
  getCookbookRole,
  COOKBOOK_ROLE_RANK,
} from "~/composables/useCookbooks";
import type { CookbookDiscussionDefault } from "~/composables/useCookbookDiscussionContext";
import type { User } from "~/composables/useAuth";
import IconSend from "~/components/icons/IconSend.vue";
import IconTrash from "~/components/icons/IconTrash.vue";

interface ChannelMessage {
  id: number;
  content: string;
  canal: string;
  author: User;
  cookbook: number;
  recipe: number | null;
  planning: number | null;
  created_at: string;
}

interface PaginatedResponse<T> {
  results: T[];
}

// Renders as a persistent right-hand sidebar from `layouts/app.vue` - see
// `useCookbookDiscussionContext` for how a page opts into showing it.
const props = defineProps<{
  cookbookId: number;
  defaultChannel: CookbookDiscussionDefault;
}>();

const { get, post, del } = useApi();
const { user } = useAuth();
const store = useCookbookStore();
const toast = useToastStore();

// Reads straight from the store (rather than a local `ref` populated once
// from `loadCookbook`'s response) so that a share/unshare elsewhere (see
// CookbookMembersPanel.vue, which mutates `store.currentCookbook` via
// `applyCookbookUpdate`) is reflected here immediately - otherwise the
// channel list/`isAlone` stayed stale until the page was reloaded.
const cookbook = computed(() =>
  store.currentCookbook?.id === props.cookbookId ? store.currentCookbook : null,
);
const isLoadingCookbook = ref(true);

const cookbookRole = computed(() =>
  cookbook.value ? getCookbookRole(cookbook.value, user.value?.id) : null,
);
// Viewing and posting both require at least "commentator" - stricter than
// the backend (which lets a reader view, just not post) but matches what's
// wanted here: a reader shouldn't see the discussion at all.
const canComment = computed(
  () =>
    !!cookbookRole.value &&
    COOKBOOK_ROLE_RANK[cookbookRole.value] >= COOKBOOK_ROLE_RANK.commentator,
);
const isCookbookAdmin = computed(() => cookbookRole.value === "admin");
// A cookbook with no one else on it (creator only, `shared_with` empty) has
// no one to discuss with - hide the panel entirely rather than show an
// empty chat only the sole member could ever post in.
const isAlone = computed(() => cookbook.value?.shared_with.length === 0);

// "general" | "recipe:<id>" | "planning:<id>" - a single string key keeps
// the <select> trivial to bind to, unpacked into {kind, id} below.
const channelKey = ref("general");

const setChannelKeyFromDefault = () => {
  channelKey.value =
    props.defaultChannel.kind === "general" || !props.defaultChannel.id
      ? "general"
      : `${props.defaultChannel.kind}:${props.defaultChannel.id}`;
};

const loadCookbook = async () => {
  isLoadingCookbook.value = true;
  try {
    await store.fetchCookbook(props.cookbookId);
  } finally {
    isLoadingCookbook.value = false;
  }
};

watch(
  () => props.cookbookId,
  () => {
    setChannelKeyFromDefault();
    loadCookbook();
  },
  { immediate: true },
);
// A page can change its own default channel (e.g. navigating from one
// recipe's edit page to another's) without the cookbook id itself
// changing - re-sync the selection whenever that happens.
watch(() => props.defaultChannel, setChannelKeyFromDefault);

const channel = computed<{
  kind: "general" | "recipe" | "planning";
  id?: number;
}>(() => {
  if (channelKey.value === "general") return { kind: "general" };
  const [kind, id] = channelKey.value.split(":");
  return { kind: kind as "recipe" | "planning", id: Number(id) };
});

const channelName = computed(() => {
  if (channel.value.kind === "recipe") {
    return cookbook.value?.recipes.find((r) => r.id === channel.value.id)
      ?.title;
  }
  if (channel.value.kind === "planning") {
    return cookbook.value?.plannings.find((p) => p.id === channel.value.id)
      ?.name;
  }
  return undefined;
});

const endpoint = computed(() => {
  if (channel.value.kind === "recipe") {
    return `/cookbooks/${props.cookbookId}/recipes/${channel.value.id}/messages/`;
  }
  if (channel.value.kind === "planning") {
    return `/cookbooks/${props.cookbookId}/plannings/${channel.value.id}/messages/`;
  }
  return `/cookbooks/${props.cookbookId}/messages/`;
});

const canalValue = computed(() => {
  if (channel.value.kind === "recipe") return "recette";
  if (channel.value.kind === "planning") return "planning";
  return "cookbook";
});

const messages = ref<ChannelMessage[]>([]);
const newMessage = ref("");
const isLoadingMessages = ref(true);
const isSending = ref(false);
const deletingId = ref<number | null>(null);

const loadMessages = async () => {
  if (!canComment.value) return;
  isLoadingMessages.value = true;
  try {
    const response = await get<PaginatedResponse<ChannelMessage>>(
      endpoint.value,
    );
    messages.value = response.results;
  } finally {
    isLoadingMessages.value = false;
  }
};

watch([canComment, endpoint], loadMessages, { immediate: true });

const send = async () => {
  const content = newMessage.value.trim();
  if (!content || isSending.value) return;
  isSending.value = true;
  try {
    const message = await post<ChannelMessage>(endpoint.value, {
      content,
      canal: canalValue.value,
    });
    messages.value = [...messages.value, message];
    newMessage.value = "";
  } finally {
    isSending.value = false;
  }
};

const canDelete = (message: ChannelMessage) =>
  message.author.id === user.value?.id || isCookbookAdmin.value;

const remove = async (message: ChannelMessage) => {
  deletingId.value = message.id;
  try {
    await del(`${endpoint.value}${message.id}/`);
    messages.value = messages.value.filter((m) => m.id !== message.id);
    toast.success("Message supprimé.");
  } finally {
    deletingId.value = null;
  }
};
</script>

<template>
  <div
    v-if="!isLoadingCookbook && canComment && !isAlone"
    class="flex h-full flex-col"
  >
    <p
      class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-400"
    >
      Discussion{{ cookbook ? ` · ${cookbook.name}` : "" }}
    </p>

    <select
      v-model="channelKey"
      class="mb-3 w-full rounded-md border border-sup-border bg-sup-withe px-2 py-[7px] text-[12.5px] font-semibold text-sup-dark-green focus:border-sup-dark-green focus:outline-none"
    >
      <option value="general">Général (tout le cookbook)</option>
      <optgroup v-if="cookbook?.recipes.length" label="Recettes">
        <option
          v-for="recipe in cookbook.recipes"
          :key="`recipe:${recipe.id}`"
          :value="`recipe:${recipe.id}`"
        >
          {{ recipe.title }}
        </option>
      </optgroup>
      <optgroup v-if="cookbook?.plannings.length" label="Plannings">
        <option
          v-for="planning in cookbook.plannings"
          :key="`planning:${planning.id}`"
          :value="`planning:${planning.id}`"
        >
          {{ planning.name }}
        </option>
      </optgroup>
    </select>

    <p
      v-if="channel.kind !== 'general'"
      class="mb-3 truncate text-[12px] text-gray-400"
      :title="channelName"
    >
      Canal de {{ channel.kind === "recipe" ? "la recette" : "du planning" }} «
      {{ channelName }} »
    </p>

    <div
      v-if="isLoadingMessages"
      class="py-6 text-center text-[12px] text-gray-400"
    >
      Chargement...
    </div>
    <div v-else class="mb-3 flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto">
      <p v-if="!messages.length" class="text-[12px] text-gray-400">
        Aucun message pour l'instant.
      </p>
      <div
        v-for="message in messages"
        :key="message.id"
        class="group text-[13px]"
      >
        <div class="flex items-baseline justify-between gap-2">
          <span class="font-semibold text-sup-very-gray">
            {{ message.author.first_name || message.author.username }}
          </span>
          <span class="flex items-center gap-1.5 text-[11px] text-gray-400">
            {{ relativeTime(message.created_at) }}
            <button
              v-if="canDelete(message)"
              type="button"
              class="text-gray-400 opacity-0 hover:text-sup-red-error group-hover:opacity-100 disabled:opacity-50"
              title="Supprimer ce message"
              :disabled="deletingId === message.id"
              @click="remove(message)"
            >
              <IconTrash size="xs" />
            </button>
          </span>
        </div>
        <p class="text-sup-very-gray">{{ message.content }}</p>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <input
        v-model="newMessage"
        type="text"
        placeholder="Écrire un message..."
        class="w-full rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13.5px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
        @keyup.enter="send"
      />
      <button
        type="button"
        class="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-md bg-sup-dark-green text-sup-withe hover:brightness-105 disabled:opacity-40"
        :disabled="!newMessage.trim() || isSending"
        @click="send"
      >
        <IconSend size="xs" />
      </button>
    </div>
  </div>
</template>
