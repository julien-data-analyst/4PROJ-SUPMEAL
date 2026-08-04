import * as z from "zod";

export const changeUsernameSchema = z.object({
  username: z
    .string()
    .min(2, "Nom d'utilisateur devrait contenir au moins 2 caractères")
    .max(
      150,
      "Nom d'utilisateur ne devrait pas contenir plus de 150 caractères",
    )
    .regex(
      /^[\w.@+-]+$/,
      "Nom d'utilisateur ne peut contenir que des lettres, chiffres et @/./+/-/_",
    ),
});

// `requirePassword` is true for OAuth-only accounts: changing their email
// also needs a new local password, since it breaks the email match OAuth
// login relies on - see ChangeEmailSerializer on the backend.
export function changeEmailSchema(requirePassword: boolean) {
  return z
    .object({
      email: z.email("Mail invalide"),
      newPassword: z.string().optional(),
      newPasswordConfirm: z.string().optional(),
    })
    .refine((data) => !requirePassword || (data.newPassword?.length ?? 0) >= 8, {
      message: "Un mot de passe d'au moins 8 caractères est requis",
      path: ["newPassword"],
    })
    .refine(
      (data) => !requirePassword || data.newPassword === data.newPasswordConfirm,
      {
        message: "Les mots de passe ne sont pas les mêmes",
        path: ["newPasswordConfirm"],
      },
    );
}

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, "Le mot de passe actuel est requis"),
    newPassword: z
      .string()
      .min(8, "Mot de passe devrait être de 8 caractères minimums"),
    newPasswordConfirm: z.string(),
  })
  .refine((data) => data.newPassword === data.newPasswordConfirm, {
    message: "Les mots de passes ne sont pas les mêmes",
    path: ["newPasswordConfirm"],
  });
