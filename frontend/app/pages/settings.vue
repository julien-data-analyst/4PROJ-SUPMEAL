<script setup lang="ts">
import AppButton from "~/components/buttons/AppButton.vue";
import AppInput from "~/components/forms/AppInput.vue";
import ConfirmModal from "~/components/common/ConfirmModal.vue";
import IconUser from "~/components/icons/IconUser.vue";
import IconCamera from "~/components/icons/IconCamera.vue";
import IconMicrosoft from "~/components/icons/IconMicrosoft.vue";
import { useAuth } from "~/composables/useAuth";
import { useUserStore } from "~/stores/useUserStore";
import { useToastStore } from "~/stores/useToastStore";
import { useOAuth } from "~/composables/useOAuth";
import { useFormValidation } from "~/composables/managingUser/useZodForm";
import { changeUsernameSchema } from "~/composables/managingUser/schemas";
import { useChangeEmail } from "~/composables/managingUser/changeemail";
import { useChangePassword } from "~/composables/managingUser/changepassword";
import { fileToDataUrl, isAllowedImageFile } from "~/composables/useRecipes";

definePageMeta({ layout: "app" });

const { user } = useAuth();
const userStore = useUserStore();
const toast = useToastStore();
const { startOAuth } = useOAuth();

const isOAuth = computed(() => user.value?.is_oauth ?? false);

onMounted(() => {
  if (useRoute().query.linked === "microsoft") {
    toast.success("Compte Microsoft lié avec succès.");
  }
});

// Avatar: pick a file -> preview it -> explicit save (the preview itself
// is the confirmation step, no popup needed here). Available to every
// account, OAuth included - it simply overrides the avatar synced from
// the provider.
const avatarInput = ref<HTMLInputElement | null>(null);
const avatarPreview = ref<string | null>(null);
const isSavingAvatar = ref(false);

const onAvatarPick = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  if (!isAllowedImageFile(file)) {
    toast.error("Format d'image non supporté. Utilisez un PNG, JPEG ou SVG.");
    return;
  }
  avatarPreview.value = await fileToDataUrl(file);
};

const cancelAvatarPreview = () => {
  avatarPreview.value = null;
  if (avatarInput.value) avatarInput.value.value = "";
};

const saveAvatar = async () => {
  if (!avatarPreview.value || isSavingAvatar.value) return;
  isSavingAvatar.value = true;
  try {
    await userStore.changeAvatar(avatarPreview.value);
    toast.success("Avatar mis à jour.");
    cancelAvatarPreview();
  } catch {
    toast.error(userStore.error || "Impossible de mettre à jour l'avatar.");
  } finally {
    isSavingAvatar.value = false;
  }
};

// Username: validate -> confirm popup -> save.
const {
  form: usernameForm,
  errors: usernameErrors,
  validate: validateUsername,
} = useFormValidation(changeUsernameSchema, {
  username: user.value?.username ?? "",
});
const usernameConfirmOpen = ref(false);
const isSavingUsername = ref(false);

const requestUsernameChange = () => {
  if (validateUsername()) usernameConfirmOpen.value = true;
};

const confirmUsernameChange = async () => {
  if (!user.value || isSavingUsername.value) return;
  isSavingUsername.value = true;
  try {
    await userStore.updateUsername(user.value.id, usernameForm.username ?? "");
    toast.success("Nom d'utilisateur mis à jour.");
  } catch {
    toast.error(
      userStore.error || "Impossible de mettre à jour le nom d'utilisateur.",
    );
  } finally {
    isSavingUsername.value = false;
    usernameConfirmOpen.value = false;
  }
};

// Email: validate -> confirm popup -> save. For an OAuth-only account this
// also creates a local password and unlinks OAuth (see useChangeEmail).
const {
  form: emailForm,
  errors: emailErrors,
  validate: validateEmail,
  submit: submitEmailChange,
} = useChangeEmail(isOAuth.value);
emailForm.email = user.value?.email ?? "";
const emailConfirmOpen = ref(false);

const requestEmailChange = () => {
  if (validateEmail()) emailConfirmOpen.value = true;
};

const confirmEmailChange = async () => {
  await submitEmailChange();
  emailConfirmOpen.value = false;
};

const emailConfirmMessage = computed(() =>
  isOAuth.value
    ? `Confirmer la nouvelle adresse email : ${emailForm.email} ? Un mot de passe local sera créé et vous ne pourrez plus vous connecter via OAuth avec ce compte.`
    : `Confirmer la nouvelle adresse email : ${emailForm.email} ?`,
);

// Password: no popup, the current-password field is itself the confirmation.
const {
  form: passwordForm,
  errors: passwordErrors,
  isSubmitting: isSavingPassword,
  submit: submitPasswordChange,
} = useChangePassword();

// Linking a Microsoft account: redirects to Microsoft, so a confirm popup
// (rather than the preview/undo patterns above) is the only way to warn the
// user before they leave the page.
const linkConfirmOpen = ref(false);

const onConfirmLinkMicrosoft = () => {
  linkConfirmOpen.value = false;
  try {
    startOAuth("microsoft", "link");
  } catch (cause) {
    toast.error(
      cause instanceof Error ? cause.message : "Liaison Microsoft impossible.",
    );
  }
};

// Account deletion.
const deleteAccountConfirmOpen = ref(false);
const isDeletingAccount = ref(false);

const confirmDeleteAccount = async () => {
  if (!user.value || isDeletingAccount.value) return;
  isDeletingAccount.value = true;
  try {
    await userStore.deleteAccount(user.value.id);
    useAuth().clearSession();
    await navigateTo("/login");
  } catch {
    toast.error(userStore.error || "Impossible de supprimer le compte.");
    deleteAccountConfirmOpen.value = false;
  } finally {
    isDeletingAccount.value = false;
  }
};
</script>

<template>
  <div class="mx-auto max-w-[560px]">
    <h1 class="mb-5 text-[22px] font-semibold text-sup-very-gray">
      Paramètres
    </h1>

    <div class="rounded-[10px] border border-sup-border bg-sup-withe p-6">
      <!-- Avatar -->
      <div class="mb-6 flex items-center gap-[14px]">
        <div
          class="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full border border-sup-border bg-sup-light-gray text-gray-400"
        >
          <img
            v-if="avatarPreview || user?.profile_icon"
            :src="avatarPreview || user?.profile_icon"
            alt=""
            class="h-full w-full object-cover"
          />
          <IconUser v-else size="lg" />
        </div>

        <div v-if="!avatarPreview" class="flex flex-col gap-1">
          <AppButton
            variant="secondary"
            size="sm"
            @click="avatarInput?.click()"
          >
            <template #icon><IconCamera size="xs" /></template>
            Changer l'avatar
          </AppButton>
          <span class="text-[11px] text-gray-400">
            PNG, JPEG ou SVG
            <template v-if="isOAuth"
              >- remplace l'avatar synchronisé depuis OAuth</template
            >
          </span>
        </div>
        <div v-else class="flex items-center gap-2">
          <AppButton
            variant="primary"
            size="sm"
            :disabled="isSavingAvatar"
            @click="saveAvatar"
          >
            {{
              isSavingAvatar ? "Enregistrement..." : "Enregistrer l'avatar"
            }}
          </AppButton>
          <AppButton variant="ghost" size="sm" @click="cancelAvatarPreview">
            Annuler
          </AppButton>
        </div>
        <input
          ref="avatarInput"
          type="file"
          accept="image/png,image/jpeg,image/svg+xml"
          class="hidden"
          @change="onAvatarPick"
        />
      </div>

      <!-- Username -->
      <div class="flex items-end gap-2">
        <div class="flex-1">
          <AppInput
            id="username"
            v-model="usernameForm.username"
            label="Nom d'utilisateur"
            :error="usernameErrors.username"
          />
        </div>
        <AppButton
          class="mb-5"
          variant="secondary"
          size="sm"
          @click="requestUsernameChange"
        >
          Enregistrer
        </AppButton>
      </div>

      <!-- Email -->
      <div class="flex items-end gap-2">
        <div class="flex-1">
          <AppInput
            id="email"
            v-model="emailForm.email"
            type="email"
            label="Email"
            :error="emailErrors.email"
          />
        </div>
        <AppButton
          class="mb-5"
          variant="secondary"
          size="sm"
          @click="requestEmailChange"
        >
          Enregistrer
        </AppButton>
      </div>

      <template v-if="isOAuth">
        <p
          class="-mt-2 mb-4 rounded-md border border-[#F0DE9A] bg-sup-yellow-warning/15 px-4 py-3 text-[12.5px] text-[#8A6D00]"
        >
          Compte connecté via OAuth : changer d'adresse email nécessite de
          créer un mot de passe local. Vous ne pourrez ensuite plus vous
          connecter via OAuth avec ce compte.
        </p>
        <AppInput
          id="email-new-password"
          v-model="emailForm.newPassword"
          type="password"
          label="Nouveau mot de passe"
          :error="emailErrors.newPassword"
        />
        <AppInput
          id="email-new-password-confirm"
          v-model="emailForm.newPasswordConfirm"
          type="password"
          label="Confirmer le mot de passe"
          :error="emailErrors.newPasswordConfirm"
        />
      </template>

      <!-- Password -->
      <template v-if="!isOAuth">
        <AppInput
          id="current-password"
          v-model="passwordForm.currentPassword"
          type="password"
          label="Mot de passe actuel"
          :error="passwordErrors.currentPassword"
        />
        <AppInput
          id="new-password"
          v-model="passwordForm.newPassword"
          type="password"
          label="Nouveau mot de passe"
          :error="passwordErrors.newPassword"
        />
        <AppInput
          id="new-password-confirm"
          v-model="passwordForm.newPasswordConfirm"
          type="password"
          label="Confirmer le nouveau mot de passe"
          :error="passwordErrors.newPasswordConfirm"
        />
        <AppButton
          variant="secondary"
          size="sm"
          :disabled="isSavingPassword"
          @click="submitPasswordChange"
        >
          {{
            isSavingPassword ? "Enregistrement..." : "Modifier le mot de passe"
          }}
        </AppButton>
      </template>
      <p
        v-else
        class="mb-5 rounded-md bg-sup-light-gray px-4 py-3 text-[12.5px] text-gray-500"
      >
        Vous êtes connecté via un compte OAuth : le mot de passe ne peut pas
        être modifié ici. Pour utiliser un mot de passe local, changez
        d'adresse email ci-dessus.
      </p>

      <!-- Comptes liés -->
      <div
        v-if="!isOAuth"
        class="mt-6 rounded-md border border-sup-border p-4"
      >
        <p class="mb-1 text-[14px] font-semibold text-sup-very-gray">
          Comptes liés
        </p>
        <p class="mb-3 text-[12.5px] text-gray-500">
          Lier un compte Microsoft vous permet de vous connecter avec celui-ci.
          Attention : une fois lié, vous ne pourrez plus vous connecter avec
          un mot de passe local, uniquement via Microsoft.
        </p>
        <AppButton
          variant="secondary"
          size="sm"
          @click="linkConfirmOpen = true"
        >
          <template #icon><IconMicrosoft size="xs" /></template>
          Lier mon compte Microsoft
        </AppButton>
      </div>

      <!-- Danger zone -->
      <div class="mt-6 rounded-md border border-red-200 bg-sup-red-error/5 p-4">
        <p class="mb-1 text-[14px] font-semibold text-sup-red-error">
          Zone de danger
        </p>
        <p class="mb-3 text-[12.5px] text-gray-500">
          La suppression de votre compte est définitive et entraîne la perte de
          toutes vos recettes, cookbooks et plannings personnels.
        </p>
        <AppButton
          variant="destructive"
          size="sm"
          @click="deleteAccountConfirmOpen = true"
        >
          Supprimer mon compte
        </AppButton>
      </div>
    </div>

    <ConfirmModal
      :open="usernameConfirmOpen"
      title="Changer de nom d'utilisateur"
      :message="`Confirmer le nouveau nom d'utilisateur : ${usernameForm.username} ?`"
      @close="usernameConfirmOpen = false"
      @confirm="confirmUsernameChange"
    />

    <ConfirmModal
      :open="emailConfirmOpen"
      title="Changer d'adresse email"
      :message="emailConfirmMessage"
      @close="emailConfirmOpen = false"
      @confirm="confirmEmailChange"
    />

    <ConfirmModal
      :open="linkConfirmOpen"
      title="Lier mon compte Microsoft"
      message="Vous allez être redirigé vers Microsoft. Une fois la liaison effectuée, vous ne pourrez plus vous connecter avec un mot de passe local : seule la connexion Microsoft fonctionnera."
      confirm-label="Continuer vers Microsoft"
      @close="linkConfirmOpen = false"
      @confirm="onConfirmLinkMicrosoft"
    />

    <ConfirmModal
      :open="deleteAccountConfirmOpen"
      title="Supprimer mon compte"
      message="Cette action est irréversible. Votre compte et toutes les données associées (recettes, cookbooks, plannings) seront définitivement supprimés."
      variant="destructive"
      confirm-label="Supprimer définitivement"
      typed-word="suppression"
      @close="deleteAccountConfirmOpen = false"
      @confirm="confirmDeleteAccount"
    />
  </div>
</template>
