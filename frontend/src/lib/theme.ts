import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark" | "auto";
const KEY = "justice.theme";

function read(): Theme {
  try {
    const t = localStorage.getItem(KEY);
    return t === "light" || t === "dark" ? t : "auto";
  } catch {
    return "auto";
  }
}

function apply(t: Theme) {
  const root = document.documentElement;
  if (t === "auto") delete root.dataset.theme;
  else root.dataset.theme = t;
  try {
    if (t === "auto") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, t);
  } catch {
    /* игнорируем */
  }
  window.dispatchEvent(new Event("justice-theme"));
}

export function isDarkNow(): boolean {
  const t = document.documentElement.dataset.theme;
  if (t) return t === "dark";
  return matchMedia("(prefers-color-scheme: dark)").matches;
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(read);
  // все компоненты, использующие тему, узнают об изменении
  useEffect(() => {
    const sync = () => setThemeState(read());
    window.addEventListener("justice-theme", sync);
    return () => window.removeEventListener("justice-theme", sync);
  }, []);
  const setTheme = useCallback((t: Theme) => apply(t), []);
  const toggle = useCallback(() => setTheme(isDarkNow() ? "light" : "dark"), [setTheme]);
  return { theme, setTheme, toggle };
}
