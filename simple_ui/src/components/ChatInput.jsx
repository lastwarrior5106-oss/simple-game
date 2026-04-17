import React from 'react';

const s = {
  inputArea: {
    padding: '16px 20px 20px',
    backgroundColor: '#16161a',
    borderTop: '1px solid #2a2a35',
  },
  form: {
    display: 'flex', alignItems: 'center', gap: '10px',
    backgroundColor: '#1e1e24', border: '1px solid #2a2a35',
    borderRadius: '14px', padding: '10px 16px',
    maxWidth: '800px', margin: '0 auto',
  },
  input: {
    flex: 1, backgroundColor: 'transparent', border: 'none',
    color: '#e8e8f0', fontSize: '15px', outline: 'none',
    fontFamily: 'sans-serif',
  },
  button: {
    backgroundColor: '#7c6aff', border: 'none', borderRadius: '9px',
    width: '36px', height: '36px', display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    cursor: 'pointer', color: '#fff',
    transition: 'background 0.18s',
  },
};

export default function ChatInput({ value, onChange, onSubmit, disabled }) {
  return (
    <div style={s.inputArea}>
      <form style={s.form} onSubmit={onSubmit}>
        <input
          type="text"
          style={s.input}
          placeholder="Mesajını buraya yaz..."
          value={value}
          onChange={e => onChange(e.target.value)}
          disabled={disabled}
        />
        <button
          type="submit"
          style={s.button}
          disabled={disabled || !value.trim()}
        >
          ➤
        </button>
      </form>
    </div>
  );
}
