import React, { useState } from 'react';
import { loginApi, registerApi } from '../api/auth';
import { useAuth } from '../context/AuthContext';

export default function AuthPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');

  const reset = () => {
    setError('');
    setSuccess('');
    setEmail('');
    setPassword('');
    setConfirmPassword('');
  };

  const switchMode = (next) => {
    reset();
    setMode(next);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (mode === 'register') {
      if (password !== confirmPassword) {
        setError('Şifreler eşleşmiyor.');
        return;
      }
      if (password.length < 6) {
        setError('Şifre en az 6 karakter olmalı.');
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === 'login') {
        const data = await loginApi(email, password);
        login(data.access_token);
        // AuthContext token'ı set edince App otomatik chat'e yönlendirir
      } else {
        await registerApi(email, password);
        setSuccess('Kayıt başarılı! Giriş yapabilirsiniz.');
        switchMode('login');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={s.page}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(24px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes glowPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(124,106,255,0); }
          50%       { box-shadow: 0 0 32px 4px rgba(124,106,255,0.18); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card { animation: fadeUp 0.55s cubic-bezier(.22,1,.36,1) both; }

        .auth-input {
          width: 100%;
          background: #0d0d0f;
          border: 1px solid #2a2a35;
          border-radius: 10px;
          color: #e8e8f0;
          font-size: 14px;
          font-family: 'DM Mono', monospace;
          padding: 13px 16px;
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .auth-input:focus {
          border-color: #7c6aff;
          box-shadow: 0 0 0 3px rgba(124,106,255,0.12);
        }
        .auth-input::placeholder { color: #44444f; }
        .auth-input:disabled { opacity: 0.5; cursor: not-allowed; }

        .auth-btn {
          width: 100%;
          padding: 13px;
          background: #7c6aff;
          color: #fff;
          border: none;
          border-radius: 10px;
          font-size: 14px;
          font-family: 'Syne', sans-serif;
          font-weight: 700;
          letter-spacing: 0.04em;
          cursor: pointer;
          transition: background 0.18s, transform 0.12s;
          animation: glowPulse 3s ease-in-out infinite;
        }
        .auth-btn:hover:not(:disabled) { background: #6a58f0; transform: translateY(-1px); }
        .auth-btn:active:not(:disabled) { transform: translateY(0); }
        .auth-btn:disabled { opacity: 0.6; cursor: not-allowed; animation: none; }

        .tab-btn {
          flex: 1;
          padding: 10px;
          background: transparent;
          border: none;
          color: #44444f;
          font-family: 'Syne', sans-serif;
          font-weight: 600;
          font-size: 13px;
          letter-spacing: 0.06em;
          cursor: pointer;
          text-transform: uppercase;
          transition: color 0.2s;
          border-bottom: 2px solid transparent;
        }
        .tab-btn.active {
          color: #e8e8f0;
          border-bottom-color: #7c6aff;
        }
        .tab-btn:hover:not(.active) { color: #a0a0b8; }

        .spinner {
          display: inline-block;
          width: 14px; height: 14px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          margin-right: 8px;
          vertical-align: middle;
        }
      `}</style>

      {/* Arka plan dekoratif unsurlar */}
      <div style={s.orb1} />
      <div style={s.orb2} />
      <div style={s.grid} />

      <div className="auth-card" style={s.card}>
        {/* Logo / Başlık */}
        <div style={s.header}>
          <div style={s.logo}>
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <polygon points="14,2 26,8 26,20 14,26 2,20 2,8" fill="none" stroke="#7c6aff" strokeWidth="1.5"/>
              <polygon points="14,7 21,11 21,17 14,21 7,17 7,11" fill="rgba(124,106,255,0.15)" stroke="#7c6aff" strokeWidth="1"/>
              <circle cx="14" cy="14" r="2.5" fill="#7c6aff"/>
            </svg>
          </div>
          <h1 style={s.title}>AI Assistant</h1>
          <p style={s.subtitle}>Devam etmek için giriş yapın</p>
        </div>

        {/* Tab Switcher */}
        <div style={s.tabs}>
          <button className={`tab-btn ${mode === 'login' ? 'active' : ''}`} onClick={() => switchMode('login')}>
            Giriş
          </button>
          <button className={`tab-btn ${mode === 'register' ? 'active' : ''}`} onClick={() => switchMode('register')}>
            Kayıt Ol
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={s.form}>
          <div style={s.fieldGroup}>
            <label style={s.label}>E-posta</label>
            <input
              className="auth-input"
              type="email"
              placeholder="ornek@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div style={s.fieldGroup}>
            <label style={s.label}>Şifre</label>
            <input
              className="auth-input"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              disabled={loading}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          {mode === 'register' && (
            <div style={s.fieldGroup}>
              <label style={s.label}>Şifre Tekrar</label>
              <input
                className="auth-input"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
                disabled={loading}
                autoComplete="new-password"
              />
            </div>
          )}

          {/* Hata / Başarı */}
          {error && (
            <div style={s.errorBox}>
              <span style={{ marginRight: 6 }}>⚠</span>{error}
            </div>
          )}
          {success && (
            <div style={s.successBox}>
              <span style={{ marginRight: 6 }}>✓</span>{success}
            </div>
          )}

          <button className="auth-btn" type="submit" disabled={loading}>
            {loading && <span className="spinner" />}
            {loading
              ? 'Lütfen bekleyin...'
              : mode === 'login' ? 'Giriş Yap' : 'Hesap Oluştur'}
          </button>
        </form>

        <p style={s.footer}>
          {mode === 'login' ? 'Hesabın yok mu? ' : 'Zaten hesabın var mı? '}
          <button
            style={s.linkBtn}
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
          >
            {mode === 'login' ? 'Kayıt ol' : 'Giriş yap'}
          </button>
        </p>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const s = {
  page: {
    minHeight: '100vh',
    backgroundColor: '#0d0d0f',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    overflow: 'hidden',
    fontFamily: "'Syne', sans-serif",
  },
  orb1: {
    position: 'absolute', top: '-120px', left: '-120px',
    width: '480px', height: '480px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(124,106,255,0.12) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  orb2: {
    position: 'absolute', bottom: '-80px', right: '-80px',
    width: '360px', height: '360px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(100,80,220,0.10) 0%, transparent 70%)',
    pointerEvents: 'none',
  },
  grid: {
    position: 'absolute', inset: 0,
    backgroundImage: `
      linear-gradient(rgba(42,42,53,0.35) 1px, transparent 1px),
      linear-gradient(90deg, rgba(42,42,53,0.35) 1px, transparent 1px)
    `,
    backgroundSize: '48px 48px',
    pointerEvents: 'none',
  },
  card: {
    position: 'relative', zIndex: 1,
    backgroundColor: '#16161a',
    border: '1px solid #2a2a35',
    borderRadius: '20px',
    padding: '40px 36px',
    width: '100%', maxWidth: '420px',
    boxShadow: '0 24px 80px rgba(0,0,0,0.5)',
  },
  header: { textAlign: 'center', marginBottom: '28px' },
  logo: {
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    width: '52px', height: '52px',
    backgroundColor: 'rgba(124,106,255,0.08)',
    borderRadius: '14px',
    border: '1px solid rgba(124,106,255,0.2)',
    marginBottom: '14px',
  },
  title: {
    fontSize: '22px', fontWeight: 800, letterSpacing: '-0.02em',
    color: '#e8e8f0', marginBottom: '6px',
  },
  subtitle: { fontSize: '13px', color: '#44444f' },
  tabs: {
    display: 'flex', borderBottom: '1px solid #2a2a35',
    marginBottom: '28px',
  },
  form: { display: 'flex', flexDirection: 'column', gap: '18px' },
  fieldGroup: { display: 'flex', flexDirection: 'column', gap: '7px' },
  label: {
    fontSize: '12px', fontWeight: 600, letterSpacing: '0.07em',
    color: '#6b6b80', textTransform: 'uppercase',
    fontFamily: "'DM Mono', monospace",
  },
  errorBox: {
    backgroundColor: '#1a1010', border: '1px solid #5a2a2a',
    color: '#ff8080', borderRadius: '8px',
    padding: '10px 14px', fontSize: '13px',
    fontFamily: "'DM Mono', monospace",
  },
  successBox: {
    backgroundColor: '#0d1a0d', border: '1px solid #2a5a2a',
    color: '#80d080', borderRadius: '8px',
    padding: '10px 14px', fontSize: '13px',
    fontFamily: "'DM Mono', monospace",
  },
  footer: { textAlign: 'center', marginTop: '22px', fontSize: '13px', color: '#44444f' },
  linkBtn: {
    background: 'none', border: 'none', color: '#7c6aff',
    cursor: 'pointer', fontSize: '13px', fontFamily: 'inherit',
    fontWeight: 600, padding: 0,
  },
};
