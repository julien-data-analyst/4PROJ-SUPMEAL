import { useFormValidation } from "./useZodForm";
import { changeEmailSchema } from "./schemas";
import { useUserStore } from "~/stores/useUserStore";
import { useToastStore } from "~/stores/useToastStore";

export function useChangeEmail() {
  const { form, errors, validate } = useFormValidation(changeEmailSchema, {
    email: "",
  });
  const userStore = useUserStore();
  const toast = useToastStore();
  const isSubmitting = ref(false);

  const submit = async (): Promise<boolean> => {
    if (!validate()) return false;

    isSubmitting.value = true;
    try {
      await userStore.changeEmail(form.email ?? "");
      toast.success("Adresse email mise à jour.");
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
