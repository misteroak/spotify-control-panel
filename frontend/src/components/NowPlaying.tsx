import type { PlaybackState } from "../api/spotify";

function formatTime(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function NowPlaying({ state }: { state: PlaybackState }) {
  if (!state.track_name) {
    return <div className="now-playing empty">No track playing</div>;
  }

  const progressPercent =
    state.duration_ms > 0 ? (state.progress_ms / state.duration_ms) * 100 : 0;

  return (
    <div className="now-playing">
      {state.album_image_url && (
        <img
          className="album-art"
          src={state.album_image_url}
          alt={state.album_name ?? "Album art"}
          width={80}
          height={80}
        />
      )}
      <div className="track-info">
        <div className="track-name">{state.track_name}</div>
        <div className="artist-name">{state.artist_name}</div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="time-display">
          <span>{formatTime(state.progress_ms)}</span>
          <span>{formatTime(state.duration_ms)}</span>
        </div>
      </div>
    </div>
  );
}
