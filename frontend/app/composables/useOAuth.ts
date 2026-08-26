import { useApi } from "./useAPI";
import { useAuth, type AuthResponse, type User } from "./useAuth";
import type { LinkMicrosoftResponse } from "~/stores/useUserStore";

type OAuthProvider = "microsoft";
// "login" signs the browser in as whichever account matches the provider's
// email (creating one if needed). "link" instead attaches the provider to
// the currently-authenticated account - see LinkMicrosoftOAuthView on the
// backend - and never touches the session's tokens.
export type OAuthMode = "login" | "link";

export interface FinishOAuthResult {
  mode: OAuthMode;
  user: User;
}

export const useOAuth = () => {
  const api = useApi();
  const { setSession, updateUser } = useAuth();
  const config = useRuntimeConfig();

  /////////////////////////////////
  // Step 1 : redirect the browser to the provider to start the flow
  /////////////////////////////////

  const startOAuth = (provider: OAuthProvider, mode: OAuthMode = "login") => {
    if (provider !== "microsoft") {
      throw new Error(`Fournisseur OAuth non supporté : ${provider}`);
    }

    if (!config.public.azureClientId) {
      throw new Error(
        "La connexion Microsoft n'est pas configurée (AZURE_CLIENT_ID manquant)",
      );
    }

    const params = new URLSearchParams({
      client_id: config.public.azureClientId,
      response_type: "code",
      redirect_uri: config.public.azureRedirectUri,
      response_mode: "query",
      scope: "openid profile email User.Read",
      // Echoed back verbatim on the callback query string - lets the
      // callback page tell a login attempt from a link attempt apart
      // without needing a second Azure app registration/redirect URI.
      state: mode,
    });

    window.location.href = `${config.public.azureAuthority}/oauth2/v2.0/authorize?${params}`;
  };

  /////////////////////////////////
  // Step 2 : finalize the OAuth provider from the callback page
  /////////////////////////////////

  const finishOAuth = async (
    provider: OAuthProvider,
  ): Promise<FinishOAuthResult> => {
    const route = useRoute();

    const code = route.query.code;
    const error = route.query.error;
    const errorDescription = route.query.error_description;
    const mode: OAuthMode = route.query.state === "link" ? "link" : "login";

    // In case of error, return it
    if (typeof error === "string" && error !== "") {
      throw new Error(
        typeof errorDescription === "string"
          ? errorDescription
          : `Connexion ${provider} refusée`,
      );
    }

    // In case of missing parameters
    if (typeof code !== "string" || code === "") {
      throw new Error("Paramètres OAuth manquants");
    }

    // Hand the code to the backend, which performs the actual exchange with Microsoft
    try {
      if (mode === "link") {
        const response = await api.post<LinkMicrosoftResponse>(
          `/users/oauth/${provider}/link/`,
          { code },
        );
        updateUser(response.user);
        return { mode, user: response.user };
      }

      const response = await api.post<AuthResponse>(
        `/users/oauth/${provider}/`,
        { code },
      );
      setSession(response);
      return { mode, user: response.user };
    } catch (cause: unknown) {
      console.error("Erreur finishOAuth:", cause);

      const e = cause as { statusCode?: number; data?: { detail?: string } };
      if (e?.statusCode === 400) {
        throw new Error(
          e.data?.detail || "La connexion a expiré, veuillez réessayer.",
          { cause },
        );
      }

      if (e?.statusCode === 401) {
        throw new Error("Authentification refusée.", { cause });
      }

      throw new Error("Une erreur est survenue pendant la connexion.", {
        cause,
      });
    }
  };

  return {
    startOAuth,
    finishOAuth,
  };
};
