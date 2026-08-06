<script setup lang="ts">
import type {
  Cookbook,
  CookbookRole,
  SharedUserCookbook,
} from "~/stores/cookbooks/useCookbookStore";
import { useCookbookStore } from "~/stores/cookbooks/useCookbookStore";
import { useToastStore } from "~/stores/useToastStore";
import { COOKBOOK_ROLE_LABELS } from "~/composables/useCookbooks";
import AppButton from "~/components/buttons/AppButton.vue";
import IconPlus from "~/components/icons/IconPlus.vue";
import IconTrash from "~/components/icons/IconTrash.vue";
import IconUser from "~/components/icons/IconUser.vue";

const props = defineProps<{
  cookbookId: number;
  creator: Cookbook["creator"];
  sharedWith: SharedUserCookbook[];
  isOwner: boolean;
}>();

type ShareableRole = Exclude<CookbookRole, "admin">;

const roleOptions: { value: ShareableRole; label: string }[] = [
  { value: "reader", label: COOKBOOK_ROLE_LABELS.reader },
  { value: "commentator", label: COOKBOOK_ROLE_LABELS.commentator },
  { value: "editor", label: COOKBOOK_ROLE_LABELS.editor },
  { value: "creator", label: COOKBOOK_ROLE_LABELS.creator },
];

const store = useCookbookStore();
const toast = useToastStore();

const showAddForm = ref(false);
const newEmail = ref("");
const newRole = ref<ShareableRole>("reader");
const isSaving = ref(false);
const savingUserId = ref<number | null>(null);
const removingUserId = ref<number | null>(null);

const addMember = async () => {
  const email = newEmail.value.trim();
  if (!email || isSaving.value) return;
  isSaving.value = true;
  try {
    await store.shareCookbook(props.cookbookId, [
      { email, role: newRole.value },
    ]);
    toast.success(`${email} a été invité(e) au cookbook.`);
    newEmail.value = "";
    newRole.value = "reader";
    showAddForm.value = false;
  } catch {
    toast.error(
      "Impossible d'ajouter cette personne. Vérifiez l'adresse e-mail.",
    );
  } finally {
    isSaving.value = false;
  }
};

const changeRole = async (userId: number, event: Event) => {
  const role = (event.target as HTMLSelectElement).value as ShareableRole;
  savingUserId.value = userId;
  try {
    await store.shareCookbook(props.cookbookId, [{ user: userId, role }]);
    toast.success("Rôle mis à jour.");
  } catch {
    toast.error("Impossible de modifier ce rôle.");
  } finally {
    savingUserId.value = null;
  }
};

const removeMember = async (userId: number) => {
  removingUserId.value = userId;
  try {
    await store.unshareCookbook(props.cookbookId, [userId]);
    toast.success("Accès retiré.");
  } catch {
    toast.error("Impossible de retirer l'accès.");
  } finally {
    removingUserId.value = null;
  }
};
</script>

<template>
  <div class="rounded-[10px] border border-sup-border bg-sup-withe">
    <div
      class="flex items-center justify-between border-b border-sup-border px-4 py-3"
    >
      <p class="text-[13px] font-semibold text-sup-very-gray">Membres</p>
      <AppButton
        v-if="isOwner"
        variant="secondary"
        size="sm"
        @click="showAddForm = !showAddForm"
      >
        <template #icon><IconPlus size="xs" /></template>
        Nouvelle personne
      </AppButton>
    </div>

    <div
      v-if="showAddForm"
      class="flex flex-wrap items-center gap-2 border-b border-sup-border px-4 py-3"
    >
      <input
        v-model="newEmail"
        type="email"
        placeholder="Adresse e-mail"
        class="min-w-[200px] flex-1 rounded-md border border-sup-border bg-sup-withe px-3 py-[9px] text-[13px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none focus:ring-2 focus:ring-sup-light-green/30"
        @keyup.enter="addMember"
      />
      <select
        v-model="newRole"
        class="rounded-md border border-sup-border bg-sup-withe px-2 py-[9px] text-[13px] text-sup-very-gray focus:border-sup-dark-green focus:outline-none"
      >
        <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
      <AppButton
        variant="primary"
        size="sm"
        :disabled="isSaving || !newEmail.trim()"
        @click="addMember"
      >
        {{ isSaving ? "Ajout..." : "Ajouter" }}
      </AppButton>
    </div>

    <ul class="divide-y divide-sup-border">
      <li class="flex items-center gap-3 px-4 py-3">
        <div
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sup-light-gray text-gray-400"
        >
          <IconUser size="xs" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[13px] font-medium text-sup-very-gray">
            {{ creator.first_name || creator.username }}
          </p>
          <p class="truncate text-[11px] text-gray-400">{{ creator.email }}</p>
        </div>
        <span
          class="shrink-0 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
        >
          Admin
        </span>
      </li>

      <li
        v-for="share in sharedWith"
        :key="share.user.id"
        class="flex items-center gap-3 px-4 py-3"
      >
        <div
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-sup-light-gray text-gray-400"
        >
          <IconUser size="xs" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="truncate text-[13px] font-medium text-sup-very-gray">
            {{ share.user.first_name || share.user.username }}
          </p>
          <p class="truncate text-[11px] text-gray-400">
            {{ share.user.email }}
          </p>
        </div>

        <select
          v-if="isOwner"
          :value="share.role"
          :disabled="savingUserId === share.user.id"
          class="shrink-0 rounded-full border border-sup-border bg-sup-withe px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green focus:border-sup-dark-green focus:outline-none disabled:opacity-50"
          @change="changeRole(share.user.id, $event)"
        >
          <option
            v-for="opt in roleOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
        <span
          v-else
          class="shrink-0 rounded-full bg-sup-light-green/15 px-[10px] py-[3px] text-[11px] font-semibold text-sup-dark-green"
        >
          {{ COOKBOOK_ROLE_LABELS[share.role] }}
        </span>

        <button
          v-if="isOwner"
          type="button"
          class="shrink-0 text-gray-400 hover:text-sup-red-error disabled:opacity-50"
          title="Retirer l'accès"
          :disabled="removingUserId === share.user.id"
          @click="removeMember(share.user.id)"
        >
          <IconTrash size="xs" />
        </button>
      </li>

      <li
        v-if="!sharedWith.length"
        class="px-4 py-6 text-center text-[12px] text-gray-400"
      >
        Ce cookbook n'est partagé avec personne pour le moment.
      </li>
    </ul>
  </div>
</template>
