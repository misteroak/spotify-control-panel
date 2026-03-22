import { useCallback, useEffect, useState } from "react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  MouseSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";
import { CheckCheck, Square, Play, CircleStop } from "lucide-react";
import { getAccounts, reorderAccounts, logout, play, pause, type Account } from "../api/spotify";
import { AccountCard } from "./AccountCard";
import { AddAccount } from "./AddAccount";

const MAX_ACCOUNTS = 5;

export function Dashboard({ userEmail }: { userEmail: string }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 300, tolerance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const loadAccounts = useCallback(async () => {
    try {
      setAccounts(await getAccounts());
    } catch {
      // API not reachable yet — will retry on next user action
    }
  }, []);

  useEffect(() => {
    loadAccounts();
  }, [loadAccounts]);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      setAccounts((prev) => {
        const oldIndex = prev.findIndex((a) => a.id === active.id);
        const newIndex = prev.findIndex((a) => a.id === over.id);
        const reordered = arrayMove(prev, oldIndex, newIndex);
        reorderAccounts(reordered.map((a) => a.id));
        return reordered;
      });
    },
    []
  );

  const handleToggleSelect = useCallback((id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleSelectAll = useCallback(() => {
    setSelectedIds((prev) => {
      if (prev.size === accounts.length) return new Set();
      return new Set(accounts.map((a) => a.id));
    });
  }, [accounts]);

  const handleStopAll = useCallback(() => {
    selectedIds.forEach((id) => pause(id));
  }, [selectedIds]);

  const handlePlayAll = useCallback(() => {
    selectedIds.forEach((id) => play(id));
  }, [selectedIds]);

  const selectedCount = selectedIds.size;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Spotify Control Panel</h1>
        <div className="header-actions">
          {accounts.length < MAX_ACCOUNTS && <AddAccount />}
          <span className="user-email">{userEmail}</span>
          <button className="logout-btn" onClick={logout}>
            Sign out
          </button>
        </div>
      </div>
      {accounts.length > 0 && (
        <div className="bulk-actions">
          <button className="bulk-btn bulk-select" onClick={handleSelectAll}>
            {selectedCount === accounts.length && selectedCount > 0
              ? <><Square size={15} /> Deselect All</>
              : <><CheckCheck size={15} /> Select All</>}
          </button>
          <div className="bulk-separator" />
          <button
            className="bulk-btn bulk-stop"
            disabled={selectedCount === 0}
            onClick={handleStopAll}
          >
            <CircleStop size={15} />
            Stop
            {selectedCount > 0 && <span className="bulk-badge bulk-badge-stop">{selectedCount}</span>}
          </button>
          <button
            className="bulk-btn bulk-play"
            disabled={selectedCount === 0}
            onClick={handlePlayAll}
          >
            <Play size={15} />
            Play
            {selectedCount > 0 && <span className="bulk-badge bulk-badge-play">{selectedCount}</span>}
          </button>
        </div>
      )}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext
          items={accounts.map((a) => a.id)}
          strategy={rectSortingStrategy}
        >
          <div className="accounts-grid">
            {accounts.map((a) => (
              <AccountCard
                key={a.id}
                account={a}
                selected={selectedIds.has(a.id)}
                onToggleSelect={handleToggleSelect}
                onRemoved={loadAccounts}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
      {accounts.length === 0 && (
        <p className="hint">
          No accounts connected yet. Click the + button to get started.
        </p>
      )}
    </div>
  );
}
