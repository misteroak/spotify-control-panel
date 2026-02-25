export function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Spotify Control Panel</h1>
        <p>Sign in with your Google account to continue.</p>
        <a href="/google/login" className="google-login-btn">
          Sign in with Google
        </a>
      </div>
    </div>
  );
}
