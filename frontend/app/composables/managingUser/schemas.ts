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

export const changeEmailSchema = z.object({
  email: z.email("Mail invalide"),
});

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
