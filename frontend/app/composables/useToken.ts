export const useToken = () => {
  const access = useState<string | null>("access-token", () => null);
  const refresh = useState<string | null>("refresh-token", () => null);
  return { access, refresh };
};
