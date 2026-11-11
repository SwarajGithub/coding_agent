import React from 'react';
import { styles } from '../styles';

export default function ExecutionLog({ steps }) {
  return (
    <div style={styles.card}>
      <label style={styles.label}>3. Agent Execution Steps ({steps.length})</label>
      <div style={styles.timelineBox}>
        {steps.length === 0 && (
          <div style={styles.emptyText}>Click "Run Agent Loop" to watch live node execution...</div>
        )}

        {steps.map((step, idx) => (
          <div key={idx} style={styles.stepItem}>
            <div style={styles.stepHeader}>
              <span style={styles.nodePill}>{step.node}</span>
              {step.retry ? <span style={styles.retryTag}>Attempt #{step.retry}</span> : null}
              <span style={styles.timeText}>{step.timestamp}</span>
            </div>

            {step.results && (
              <pre
                style={{
                  ...styles.tracePre,
                  borderLeftColor: step.results.includes('FAILED') ? '#ef4444' : '#10b981',
                }}
              >
                {step.results}
              </pre>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
