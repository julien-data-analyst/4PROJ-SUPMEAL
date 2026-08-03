// stores/useUserStore.ts
import { defineStore } from "pinia";
import { useApi } from "~/composables/useAPI";
import { useAuth, type User } from "~/composables/useAuth";

export interface ChangeEmailResponse {
  detail: string;
  email: string;
}

export interface ChangePasswordResponse {
  detail: string;
}

export interface ChangeAvatarResponse {
  detail: string;
  profile_icon: string;
}

export const useUserStore = defineStore("user", () => {
  const { post, patch, del } = useApi();

  const loading = ref(false);
  const error = ref<string | null>(null);

  const updateUsername = async (
    id: number,
    username: string,
  ): Promise<User> => {
    loading.value = true;
    error.value = null;
    try {
      const result = await patch<User>(`/users/${id}/`, { username });
      useAuth().updateUser({ username: result.username });
      return result;
    } catch (cause) {
      error.value = "Impossible de mettre à jour le nom d'utilisateur.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const changeEmail = async (
    newEmail: string,
  ): Promise<ChangeEmailResponse> => {
    loading.value = true;
    error.value = null;
    try {
      const result = await post<ChangeEmailResponse>("/users/change-email/", {
        new_email: newEmail,
      });
      useAuth().updateUser({ email: result.email });
      return result;
    } catch (cause) {
      error.value = "Impossible de mettre à jour l'adresse email.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const changePassword = async (
    currentPassword: string,
    newPassword: string,
  ): Promise<ChangePasswordResponse> => {
    loading.value = true;
    error.value = null;
    try {
      return await post<ChangePasswordResponse>("/users/change-password/", {
        current_password: currentPassword,
        new_password: newPassword,
      });
    } catch (cause) {
      error.value = "Impossible de mettre à jour le mot de passe.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const changeAvatar = async (
    dataUri: string,
  ): Promise<ChangeAvatarResponse> => {
    loading.value = true;
    error.value = null;
    try {
      const result = await post<ChangeAvatarResponse>("/users/change-avatar/", {
        avatar: dataUri,
      });
      useAuth().updateUser({ profile_icon: result.profile_icon });
      return result;
    } catch (cause) {
      error.value = "Impossible de mettre à jour l'avatar.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  const deleteAccount = async (id: number): Promise<void> => {
    loading.value = true;
    error.value = null;
    try {
      await del(`/users/${id}/`);
    } catch (cause) {
      error.value = "Impossible de supprimer le compte.";
      throw cause;
    } finally {
      loading.value = false;
    }
  };

  return {
    loading,
    error,
    updateUsername,
    changeEmail,
    changePassword,
    changeAvatar,
    deleteAccount,
  };
});
