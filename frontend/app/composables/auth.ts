import * as z from "zod";

export const loginSchema = z.object({
  email: z.email("Mail invalide"),
  password: z
    .string()
    .min(8, "Mot de passe devrait être de 8 caractères minimums"),
});

export const registerSchema = loginSchema
  .extend({
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
    passwordConfirm: z.string(),
  })
  .refine((data) => data.password === data.passwordConfirm, {
    message: "Les mots de passes ne sont pas les mêmes",
    path: ["passwordConfirm"],
  });
