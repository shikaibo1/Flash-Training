// Storage can be unavailable in private mode or full. That must not invalidate a
// successfully created server-side session or discard a returned evaluation.
export const sessionCache = {
  read(key: string): string | null {
    try { return sessionStorage.getItem(key); } catch { return null; }
  },
  write(key: string, value: string): boolean {
    try { sessionStorage.setItem(key, value); return true; } catch { return false; }
  },
  remove(key: string): void {
    try { sessionStorage.removeItem(key); } catch { /* No storage to clean up. */ }
  },
};
