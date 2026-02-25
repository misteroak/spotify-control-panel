import { useCallback, useEffect, useState } from "react";
import { getAccounts, type Account } from "../api/spotify";
import { AccountCard } from "./AccountCard";
import { AddAccount } from "./AddAccount";

const MAX_ACCOUNTS = 5;

export function Dashboard() {
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
        {accounts.length < MAX_ACCOUNTS && <AddAccount />}
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
