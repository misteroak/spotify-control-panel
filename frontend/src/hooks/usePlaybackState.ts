import { useEffect, useRef, useState } from "react";
import { getPlaybackState, type PlaybackState } from "../api/spotify";

export function usePlaybackState(accountId: number, intervalMs = 2000) {
  const [state, setState] = useState<PlaybackState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    const poll = async () => {
      try {
        const s = await getPlaybackState(accountId);
        if (mountedRef.current) {
          setState(s);
          setError(null);
        }
      } catch (e) {
        if (mountedRef.current) {
          setError(e instanceof Error ? e.message : "Unknown error");
        }
      }
    };

    poll();
    const id = setInterval(poll, intervalMs);

    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [accountId, intervalMs]);

  return { state, error };
}
