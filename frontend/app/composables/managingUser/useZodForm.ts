import type * as z from "zod";

export function useFormValidation<T extends z.ZodTypeAny>(
  schema: T,
  initial: Record<string, string>,
) {
  const form = reactive<Record<string, string>>({ ...initial });
  const errors = reactive<Record<string, string | undefined>>({});

  function validate(): boolean {
    const result = schema.safeParse(form);

    Object.keys(errors).forEach((k) => (errors[k] = undefined));

    if (!result.success) {
      for (const issue of result.error.issues) {
        const key = String(issue.path[0]);
        if (key && errors[key] === undefined) {
          errors[key] = issue.message;
        }
      }
      return false;
    }

    return true;
  }

  return { form, errors, validate };
}
