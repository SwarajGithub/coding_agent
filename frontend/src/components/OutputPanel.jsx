import React, { useState } from 'react';
import { styles } from '../styles';

export default function OutputPanel({ finalCode, judgeReport }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(finalCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <div style={styles.card}>
        <div style={styles.rowBetween}>
          <label style={styles.label}>4. Final Solution Code (solution.py)</label>
          {finalCode && (
            <button style={styles.copyBtn} onClick={handleCopy}>
              {copied ? '✓ Copied' : 'Copy Code'}
            </button>
          )}
        </div>
        <pre style={styles.codeBlock}>
          {finalCode || '# Verified Python implementation will appear here...'}
        </pre>
      </div>

      {judgeReport && (
        <div style={{ ...styles.card, borderColor: '#3b82f6' }}>
          <label style={styles.label}>5. LLM-as-a-Judge Quality Audit</label>
          <pre style={styles.judgeBlock}>{judgeReport}</pre>
        </div>
      )}
    </>
  );
}
