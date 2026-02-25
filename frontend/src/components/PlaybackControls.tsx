import {
  nextTrack,
  pause,
  play,
  previousTrack,
  seek,
  setVolume,
  type PlaybackState,
} from "../api/spotify";

interface Props {
  accountId: number;
  state: PlaybackState;
}

export function PlaybackControls({ accountId, state }: Props) {
  const handlePlayPause = () => {
    if (state.is_playing) {
      pause(accountId);
    } else {
      play(accountId);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setVolume(accountId, Number(e.target.value));
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    seek(accountId, Number(e.target.value));
  };

  return (
    <div className="playback-controls">
      <div className="transport-buttons">
        <button onClick={() => previousTrack(accountId)} title="Previous">
          &#9198;
        </button>
        <button onClick={handlePlayPause} title={state.is_playing ? "Pause" : "Play"}>
          {state.is_playing ? "\u23F8" : "\u25B6"}
        </button>
        <button onClick={() => nextTrack(accountId)} title="Next">
          &#9197;
        </button>
      </div>

      <div className="seek-control">
        <input
          type="range"
          min={0}
          max={state.duration_ms}
          value={state.progress_ms}
          onChange={handleSeek}
          title="Seek"
        />
      </div>

      <div className="volume-control">
        <label>Vol</label>
        <input
          type="range"
          min={0}
          max={100}
          value={state.volume_percent ?? 0}
          disabled={state.volume_percent === null}
          onChange={handleVolumeChange}
          title="Volume"
        />
        <span>{state.volume_percent ?? "—"}%</span>
      </div>

      {state.device_name && (
        <div className="device-name">Playing on: {state.device_name}</div>
      )}
    </div>
  );
}
