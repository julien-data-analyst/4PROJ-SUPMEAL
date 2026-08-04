import { useFormValidation } from "./useZodForm";
import { changeEmailSchema } from "./schemas";
import { useUserStore } from "~/stores/useUserStore";
import { useToastStore } from "~/stores/useToastStore";

// `isOAuth` is fixed for the composable's lifetime - it reflects the account's
// state when the settings page loaded, which is enough since a successful
// submit here is precisely what would change it (and navigates away/reloads
// the relevant state afterwards).
export function useChangeEmail(isOAuth: boolean) {
  const { form, errors, validate } = useFormValidation(
    changeEmailSchema(isOAuth),
    { email: "", newPassword: "", newPasswordConfirm: "" },
  );
  const userStore = useUserStore();
  const toast = useToastStore();
  const isSubmitting = ref(false);

  const submit = async (): Promise<boolean> => {
    if (!validate()) return false;

    isSubmitting.value = true;
    try {
      await userStore.changeEmail(
        form.email ?? "",
        isOAuth ? form.newPassword : undefined,
      );
      form.newPassword = "";
      form.newPasswordConfirm = "";
      toast.success(
        isOAuth
          ? "Adresse email mise à jour. Un mot de passe local a été créé : vous ne pouvez plus vous connecter via OAuth avec ce compte."
          : "Adresse email mise à jour.",
      );
      return true;
    } catch {
      toast.error(
        userStore.error || "Impossible de mettre à jour l'adresse email.",
      );
      return false;
    } finally {
      isSubmitting.value = false;
    }
  };

  return { form, errors, isSubmitting, validate, submit };
}
