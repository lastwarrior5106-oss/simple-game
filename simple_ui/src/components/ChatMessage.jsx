import React from 'react';

const s = {
  row: { display: 'flex' },
  userRow: { justifyContent: 'flex-end' },
  botRow: { justifyContent: 'flex-start' },
  wrapper: { display: 'flex', flexDirection: 'column' },
  status: {
    fontSize: '12px', color: '#6b6b80',
    marginBottom: '4px', marginLeft: '4px', fontStyle: 'italic',
  },
  bubble: {
    padding: '12px 18px', borderRadius: '18px', maxWidth: '75%',
    lineHeight: '1.6', fontSize: '15px',
    whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  },
  userBubble: { backgroundColor: '#7c6aff', color: '#fff', borderBottomRightRadius: '4px' },
  botBubble: {
    backgroundColor: '#16161a', border: '1px solid #2a2a35',
    color: '#e8e8f0', borderBottomLeftRadius: '4px',
  },
  errorBubble: {
    backgroundColor: '#1a1010', border: '1px solid #5a2a2a',
    color: '#ff8080', borderBottomLeftRadius: '4px',
  },
  cursor: {
    display: 'inline-block', width: '2px', height: '1em',
    backgroundColor: '#7c6aff', marginLeft: '2px',
    verticalAlign: 'text-bottom', animation: 'cursorBlink 0.8s step-end infinite',
  },
};

export default function ChatMessage({ msg, activeNode }) {
  const isUser = msg.sender === 'user';

  const bubbleStyle = isUser
    ? { ...s.bubble, ...s.userBubble }
    : msg.error
    ? { ...s.bubble, ...s.errorBubble }
    : { ...s.bubble, ...s.botBubble };

  return (
    <div style={{ ...s.row, ...(isUser ? s.userRow : s.botRow) }}>
      <div style={s.wrapper}>
        {!isUser && msg.streaming && activeNode && (
          <div style={s.status}>
            {activeNode}
            {' '}<span className="dot" /><span className="dot" /><span className="dot" />
          </div>
        )}
        <div style={bubbleStyle}>
          {msg.text}
          {msg.streaming && <span style={s.cursor} />}
        </div>
      </div>
    </div>
  );
}
