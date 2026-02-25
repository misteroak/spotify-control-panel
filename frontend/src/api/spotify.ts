export interface Account {
  id: number;
  spotify_user_id: string;
  display_name: string;
}

export interface PlaybackState {
  is_playing: boolean;
  track_name: string | null;
  artist_name: string | null;
  album_name: string | null;
  album_image_url: string | null;
  progress_ms: number;
  duration_ms: number;
  volume_percent: number | null;
  device_name: string | null;
}

const BASE = "";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, options);
  if (resp.status === 401) {
    window.location.href = "/google/login";
    throw new Error("Not authenticated");
  }
  if (!resp.ok) throw new Error(`API error: ${resp.status}`);
  return resp.json();
}

export async function checkAuth(): Promise<{ email: string } | null> {
  try {
    const resp = await fetch(`${BASE}/google/me`);
    if (!resp.ok) return null;
    return resp.json();
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  await fetch(`${BASE}/google/logout`, { method: "POST" });
  window.location.href = "/google/login";
}

export async function getAccounts(): Promise<Account[]> {
  return api("/auth/accounts");
}

export async function deleteAccount(accountId: number): Promise<void> {
  await api(`/auth/accounts/${accountId}`, { method: "DELETE" });
}

export async function reorderAccounts(orderedIds: number[]): Promise<void> {
  await api("/auth/accounts/reorder", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orderedIds),
  });
}

export async function getPlaybackState(
  accountId: number
): Promise<PlaybackState> {
  return api(`/playback/${accountId}/state`);
}

export async function play(accountId: number): Promise<void> {
  await api(`/playback/${accountId}/play`, { method: "PUT" });
}

export async function pause(accountId: number): Promise<void> {
  await api(`/playback/${accountId}/pause`, { method: "PUT" });
}

export async function setVolume(
  accountId: number,
  level: number
): Promise<void> {
  const params = new URLSearchParams({ level: String(level) });
  await api(`/playback/${accountId}/volume?${params}`, { method: "PUT" });
}

export async function seek(
  accountId: number,
  positionMs: number
): Promise<void> {
  const params = new URLSearchParams({ position_ms: String(positionMs) });
  await api(`/playback/${accountId}/seek?${params}`, { method: "PUT" });
}

export async function nextTrack(accountId: number): Promise<void> {
  await api(`/playback/${accountId}/next`, { method: "POST" });
}

export async function previousTrack(accountId: number): Promise<void> {
  await api(`/playback/${accountId}/previous`, { method: "POST" });
}
