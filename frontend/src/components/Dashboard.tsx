import { useCallback, useEffect, useState } from "react";
import { getAccounts, logout, type Account } from "../api/spotify";
import { AccountCard } from "./AccountCard";
import { AddAccount } from "./AddAccount";

const MAX_ACCOUNTS = 5;

export function Dashboard({ userEmail }: { userEmail: string }) {
  const [accounts, setAccounts] = useState<Account[]>([]);

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
      <div className="accounts-grid">
        {accounts.map((a) => (
          <AccountCard key={a.id} account={a} onRemoved={loadAccounts} />
        ))}
      </div>
      {accounts.length === 0 && (
        <p className="hint">
          No accounts connected yet. Click the + button to get started.
        </p>
      )}
    </div>
  );
}
