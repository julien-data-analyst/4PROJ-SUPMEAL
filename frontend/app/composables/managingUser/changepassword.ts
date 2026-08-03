import { useFormValidation } from "./useZodForm";
import { changePasswordSchema } from "./schemas";
import { useUserStore } from "~/stores/useUserStore";
import { useToastStore } from "~/stores/useToastStore";

export function useChangePassword() {
  const { form, errors, validate } = useFormValidation(changePasswordSchema, {
    currentPassword: "",
    newPassword: "",
    newPasswordConfirm: "",
  });
  const userStore = useUserStore();
  const toast = useToastStore();
  const isSubmitting = ref(false);

  const submit = async (): Promise<boolean> => {
    if (!validate()) return false;

    isSubmitting.value = true;
    try {
      await userStore.changePassword(
        form.currentPassword ?? "",
        form.newPassword ?? "",
      );
      form.currentPassword = "";
      form.newPassword = "";
      form.newPasswordConfirm = "";
      toast.success("Mot de passe mis à jour.");
      return true;
    } catch {
      toast.error(
        userStore.error || "Impossible de mettre à jour le mot de passe.",
      );
      return false;
    } finally {
      isSubmitting.value = false;
    }
  };

  return { form, errors, isSubmitting, submit };
}
