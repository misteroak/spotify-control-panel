import type { CSSProperties } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Account } from "../api/spotify";
import { deleteAccount } from "../api/spotify";
import { usePlaybackState } from "../hooks/usePlaybackState";
import { NowPlaying } from "./NowPlaying";
import { PlaybackControls } from "./PlaybackControls";

interface Props {
  account: Account;
  selected: boolean;
  onToggleSelect: (id: number) => void;
  onRemoved: () => void;
}

const INTERACTIVE = "button, input, a, [role='slider']";

export function AccountCard({ account, selected, onToggleSelect, onRemoved }: Props) {
  const { state, error } = usePlaybackState(account.id);
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: account.id });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleRemove = async () => {
    await deleteAccount(account.id);
    onRemoved();
  };

  const handleCardClick = (e: React.MouseEvent | React.TouchEvent) => {
    // Don't toggle selection when tapping interactive controls
    if ((e.target as HTMLElement).closest(INTERACTIVE)) return;
    onToggleSelect(account.id);
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`account-card${selected ? " selected" : ""}${isDragging ? " dragging" : ""}`}
      onClick={handleCardClick}
      {...attributes}
      {...listeners}
    >
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
