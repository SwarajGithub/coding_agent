import React from 'react';
import { styles, badgeColors } from '../styles';

export default function Header({ status }) {
  return (
    <header style={styles.header}>
      <div>
        <h1 style={styles.title}>Autonomous TDD Coding Agent</h1>
        <span style={styles.subtitle}>LangGraph Dual-Healing Loop + LLM-as-a-Judge</span>
      </div>
      <span style={{ ...styles.badge, ...badgeColors[status] }}>{status}</span>
    </header>
  );
}
