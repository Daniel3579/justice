const base = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export const PanelIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base}><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M9 4v16" /></svg>
);
export const PlusIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base}><path d="M12 5v14M5 12h14" /></svg>
);
export const CloseIcon = ({ size = 14 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" {...base} strokeWidth={2}><path d="M18 6 6 18M6 6l12 12" /></svg>
);
export const ArrowUpIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" {...base} strokeWidth={2.2}><path d="M12 19V5M5 12l7-7 7 7" /></svg>
);
export const UserIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...base}><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0 1 16 0" /></svg>
);
export const MoonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...base}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>
);
export const LogoutIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" {...base}><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l-5-5 5-5M5 12h11" /></svg>
);
export const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" {...base}><rect x="9" y="9" width="12" height="12" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>
);
export const DownloadIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" {...base}><path d="M12 4v12m0 0-4-4m4 4 4-4M5 20h14" /></svg>
);
