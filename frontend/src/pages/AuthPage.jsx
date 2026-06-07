import { useEffect, useRef, useState } from "react";

import { api } from "../api";

const roles = [
  { value: "buyer", label: "Buyer", hint: "Shop, save addresses, review orders, and ask the assistant." },
  { value: "seller", label: "Seller", hint: "Manage products, stock, orders, and review responses." },
];

const GOOGLE_SCRIPT_ID = "google-identity-services";
const GOOGLE_SCRIPT_SRC = "https://accounts.google.com/gsi/client";

function loadGoogleIdentityScript() {
  if (window.google?.accounts?.id) return Promise.resolve();

  const existingScript = document.getElementById(GOOGLE_SCRIPT_ID);
  if (existingScript) {
    return new Promise((resolve, reject) => {
      existingScript.addEventListener("load", resolve, { once: true });
      existingScript.addEventListener("error", reject, { once: true });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.id = GOOGLE_SCRIPT_ID;
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

export default function AuthPage({ onLogin, onBack, authUser }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState(authUser?.name || "");
  const [email, setEmail] = useState(authUser?.email || "");
  const [phone, setPhone] = useState(authUser?.phone || "");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(authUser?.role === "seller" ? "seller" : "buyer");
  const [message, setMessage] = useState("Sign in or create an account to continue shopping.");
  const [busy, setBusy] = useState(false);
  const [googleStatus, setGoogleStatus] = useState("");
  const googleButtonRef = useRef(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const response = mode === "signup"
        ? await api.signup({ name, email, phone, password })
        : await api.login({ email, password });
      onLogin(response);
    } catch (err) {
      setMessage(err.message || "Authentication failed");
    } finally {
      setBusy(false);
    }
  };

  const handleGoogleCredential = async (response) => {
    if (!response?.credential) {
      setMessage("Google did not return a credential. Try again.");
      return;
    }

    setBusy(true);
    setMessage("");
    try {
      const loginResponse = await api.oauth({ credential: response.credential, provider: "google", role });
      onLogin(loginResponse);
    } catch (err) {
      setMessage(err.message || "Google sign-in failed");
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    let cancelled = false;

    if (!googleClientId) {
      setGoogleStatus("Set VITE_GOOGLE_CLIENT_ID in frontend/.env to enable Google sign-in.");
      return () => { cancelled = true; };
    }

    setGoogleStatus("Loading Google sign-in...");
    loadGoogleIdentityScript()
      .then(() => {
        if (cancelled || !googleButtonRef.current || !window.google?.accounts?.id) return;
        googleButtonRef.current.innerHTML = "";
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: handleGoogleCredential,
        });
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          text: mode === "signup" ? "signup_with" : "signin_with",
          width: Math.min(380, googleButtonRef.current.offsetWidth || 340),
        });
        setGoogleStatus("");
      })
      .catch(() => {
        if (!cancelled) setGoogleStatus("Google sign-in could not load. Check your internet connection.");
      });

    return () => {
      cancelled = true;
    };
  }, [googleClientId, mode, role]);

  return (
    <main className="auth-page">
      <section className="auth-promo">
        <span className="auth-badge">Account</span>
        <h1>Sign in, choose your role, and continue shopping.</h1>
        <p>Manage your cart, orders, addresses, payments, and seller tools from one secure account.</p>
        <ul className="auth-points">
          <li>Buyer accounts can shop, review orders, save addresses, and manage carts.</li>
          <li>Seller accounts can manage products, inventory, orders, and reviews.</li>
          <li>Secure Google sign-in is available after choosing your account role.</li>
        </ul>
      </section>

      <section className="surface auth-card">
        <button type="button" className="text-button back-button" onClick={onBack}>Back to catalog</button>
        <div className="section-header compact auth-header">
          <div>
            <span className="eyebrow">{mode === "signup" ? "Create account" : "Welcome back"}</span>
            <h2>{mode === "signup" ? "Signup" : "Login"}</h2>
            <p>{message || "Enter your details to continue."}</p>
          </div>
        </div>

        <form className="auth-form" onSubmit={submit}>
          <div className="tab-strip">
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button>
            <button type="button" className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")}>Signup</button>
          </div>

          <div className="role-switch" role="tablist" aria-label="Choose account role">
            {roles.map((item) => (
              <button key={item.value} type="button" className={item.value === role ? "role-option active" : "role-option"} onClick={() => setRole(item.value)}>
                <strong>{item.label}</strong>
                <span>{item.hint}</span>
              </button>
            ))}
          </div>

          {mode === "signup" ? (
            <div className="form-grid two-up">
              <label><span>Name</span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your full name" /></label>
              <label><span>Phone</span><input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Mobile number" /></label>
            </div>
          ) : null}

          <label><span>Email</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></label>
          <label><span>Password</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" /></label>

          <div className="auth-actions">
            <button type="submit" className="primary-button" disabled={busy}>{busy ? "Working..." : "Continue"}</button>
          </div>

          <div className="google-oauth-panel">
            <p>Choose Buyer or Seller above, then continue with Google.</p>
            <div className="google-button-shell" ref={googleButtonRef} aria-live="polite" />
            {googleStatus ? <span className="oauth-help">{googleStatus}</span> : null}
          </div>
        </form>
      </section>
    </main>
  );
}
