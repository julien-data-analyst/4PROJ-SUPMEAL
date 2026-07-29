export default defineNuxtRouteMiddleware(async (to) => {
  const { initAuth, isAuthenticated } = useAuth();
  await initAuth();

  // Reachable without being authenticated.
  const publicRoutes = [
    "/public_home",
    "/login",
    "/register",
    "/logout",
    "/connect/microsoft/callback",
  ];
  // Redirect an already-authenticated user away from these (they only make sense signed out).
  const guestOnlyRoutes = ["/public_home", "/login", "/register"];

  const isShareLinkRoute = to.path.startsWith("/s/");
  const isResetPasswordRoute = to.path.startsWith("/reset-password/");

  if (
    !isAuthenticated.value &&
    !publicRoutes.includes(to.path) &&
    !isShareLinkRoute &&
    !isResetPasswordRoute
  ) {
    return navigateTo("/public_home");
  }

  if (isAuthenticated.value && guestOnlyRoutes.includes(to.path)) {
    return navigateTo("/home");
  }
});
