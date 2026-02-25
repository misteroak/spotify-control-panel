import type { Account } from "../api/spotify";
import { deleteAccount } from "../api/spotify";
import { usePlaybackState } from "../hooks/usePlaybackState";
import { NowPlaying } from "./NowPlaying";
import { PlaybackControls } from "./PlaybackControls";

interface Props {
  account: Account;
  onRemoved: () => void;
}

export function AccountCard({ account, onRemoved }: Props) {
  const { state, error } = usePlaybackState(account.id);

  const handleRemove = async () => {
    await deleteAccount(account.id);
    onRemoved();
  };

  return (
    <div className="account-card">
      <div className="account-header">
        <h3>{account.display_name}</h3>
        <button className="remove-btn" onClick={handleRemove} title="Remove account">
          &times;
        </button>
      </div>

      {error && <div className="error">Error: {error}</div>}

      {state ? (
        <>
          <NowPlaying state={state} />
          <PlaybackControls accountId={account.id} state={state} />
        </>
      ) : (
        !error && <div className="loading">Loading...</div>
      )}
    </div>
  );
}
