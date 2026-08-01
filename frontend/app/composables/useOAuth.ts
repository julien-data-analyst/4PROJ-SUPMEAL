import { useApi } from "./useAPI";
import { useAuth, type AuthResponse } from "./useAuth";

type OAuthProvider = "microsoft";

export const useOAuth = () => {
  const api = useApi();
  const { setSession } = useAuth();
  const config = useRuntimeConfig();

  /////////////////////////////////
  // Step 1 : redirect the browser to the provider to start the flow
  /////////////////////////////////

  const startOAuth = (provider: OAuthProvider) => {
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
    });

    window.location.href = `${config.public.azureAuthority}/oauth2/v2.0/authorize?${params}`;
  };

  /////////////////////////////////
  // Step 2 : finalize the OAuth provider from the callback page
  /////////////////////////////////

  const finishOAuth = async (provider: OAuthProvider) => {
    const route = useRoute();

    const code = route.query.code;
    const error = route.query.error;
    const errorDescription = route.query.error_description;

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
      const response = await api.post<AuthResponse>(
        `/users/oauth/${provider}/`,
        { code },
      );
      setSession(response);
      return response.user;
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
