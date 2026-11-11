import React from 'react';
import { styles } from '../styles';

export default function InputPanel({
  requirement,
  setRequirement,
  testSuite,
  setTestSuite,
  maxRetries,
  setMaxRetries,
  isRunning,
  onRun,
  onStop,
}) {
  return (
    <div style={styles.column}>
      <div style={styles.card}>
        <label style={styles.label}>1. Coding Requirement / Feature Spec</label>
        <textarea
          style={styles.textarea}
          rows={7}
          value={requirement}
          onChange={(e) => setRequirement(e.target.value)}
          disabled={isRunning}
          placeholder="Describe the function or class you want the agent to build..."
        />
      </div>

      <div style={styles.card}>
        <div style={styles.rowBetween}>
          <label style={styles.label}>2. Pytest Verification Suite (test_solution.py)</label>
          <span style={styles.hint}>Auto-heals if syntax is broken</span>
        </div>
        <textarea
          style={{ ...styles.textarea, fontFamily: 'monospace', fontSize: '13px' }}
          rows={13}
          value={testSuite}
          onChange={(e) => setTestSuite(e.target.value)}
          disabled={isRunning}
          placeholder="Write your pytest assertions here..."
        />
      </div>

      <div style={styles.controlsBar}>
        <div style={styles.retryGroup}>
          <label style={styles.labelInline}>Max Retries:</label>
          <input
            type="number"
            min={1}
            max={10}
            value={maxRetries}
            onChange={(e) => setMaxRetries(e.target.value)}
            disabled={isRunning}
            style={styles.numberInput}
          />
        </div>

        {!isRunning ? (
          <button style={styles.runBtn} onClick={onRun}>
            ▶ Run Agent Loop
          </button>
        ) : (
          <button style={styles.stopBtn} onClick={onStop}>
            ■ Stop Execution
          </button>
        )}
      </div>
    </div>
  );
}
