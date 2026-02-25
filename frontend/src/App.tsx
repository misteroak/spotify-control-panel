import { useEffect, useState } from "react";
import { checkAuth } from "./api/spotify";
import { Dashboard } from "./components/Dashboard";
import { LoginPage } from "./components/LoginPage";
import "./App.css";

export default function App() {
  const [user, setUser] = useState<{ email: string } | null | undefined>(
    undefined
  );

  useEffect(() => {
    checkAuth().then(setUser);
  }, []);

  if (user === undefined) {
    return <div className="auth-loading">Loading...</div>;
  }

  if (user === null) {
    return <LoginPage />;
  }

  return <Dashboard userEmail={user.email} />;
}
