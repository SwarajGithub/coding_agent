import React, { useState, useRef } from 'react';
import Header from './components/Header';
import InputPanel from './components/InputPanel';
import ExecutionLog from './components/ExecutionLog';
import OutputPanel from './components/OutputPanel';
import { streamAgentExecution } from './services/agentStream';
import { styles } from './styles';

const DEFAULT_REQUIREMENT = `Write a class named 'TransactionProcessor' with a method 'process_ledger(transactions: list) -> dict'.
It must take a list of dictionaries, filter out any dictionary missing an 'amount' key, sum up amounts grouped by 'category', and return:
{'total_processed': float, 'categories': dict}.
If an empty list is passed, return {'total_processed': 0.0, 'categories': {}}.`;

const DEFAULT_TESTS = `import pytest
from solution import TransactionProcessor

def test_empty_ledger():
    tp = TransactionProcessor()
    assert tp.process_ledger([]) == {'total_processed': 0.0, 'categories': {}}

def test_valid_ledger():
    tp = TransactionProcessor()
    data = [
        {'id': 1, 'category': 'food', 'amount': 12.50},
        {'id': 2, 'category': 'utilities', 'amount': 85.00},
        {'id': 3, 'category': 'food', 'amount': 7.50}
    ]
    res = tp.process_ledger(data)
    assert res['total_processed'] == 105.00
    assert res['categories']['food'] == 20.00`;

export default function App() {
  const [requirement, setRequirement] = useState(DEFAULT_REQUIREMENT);
  const [testSuite, setTestSuite] = useState(DEFAULT_TESTS);
  const [maxRetries, setMaxRetries] = useState(5);
  const [isRunning, setIsRunning] = useState(false);
  const [steps, setSteps] = useState([]);
  const [finalCode, setFinalCode] = useState('');
  const [judgeReport, setJudgeReport] = useState('');
  const [status, setStatus] = useState('IDLE');

  const abortControllerRef = useRef(null);

  const handleEvent = (eventData) => {
    if (eventData.status === 'COMPLETED') {
      setStatus((prev) => (prev === 'PASSED' ? 'PASSED' : 'COMPLETED'));
      return;
    }
    if (eventData.status === 'ERROR') {
      setStatus('ERROR');
      setSteps((prev) => [
        ...prev,
        { node: 'error', timestamp: new Date().toLocaleTimeString(), results: eventData.error },
      ]);
      return;
    }

    const nodeName = Array.isArray(eventData.node) ? eventData.node[0] : eventData.node;

    if (eventData.code_draft) setFinalCode(eventData.code_draft);
    if (nodeName === 'fix_test_suite' && eventData.test_suite) setTestSuite(eventData.test_suite);

    if (nodeName === 'evaluate_quality' && eventData.test_results) {
      setJudgeReport(eventData.test_results);
      setStatus('PASSED');
    } else if (nodeName === 'run_tests' && eventData.test_results?.startsWith('PASSED')) {
      setStatus('PASSED');
    }

    setSteps((prev) => [
      ...prev,
      {
        node: nodeName,
        retry: eventData.retry_count,
        timestamp: new Date().toLocaleTimeString(),
        results: eventData.test_results,
      },
    ]);
  };

  const handleRun = async () => {
    setIsRunning(true);
    setSteps([]);
    setFinalCode('');
    setJudgeReport('');
    setStatus('RUNNING');
    abortControllerRef.current = new AbortController();

    try {
      await streamAgentExecution({
        payload: { requirement, test_suite: testSuite, max_retries: Number(maxRetries) },
        signal: abortControllerRef.current.signal,
        onEvent: handleEvent,
      });
    } catch (err) {
      if (err.name !== 'AbortError') {
        setStatus('ERROR');
        setSteps((prev) => [
          ...prev,
          { node: 'network_error', timestamp: new Date().toLocaleTimeString(), results: err.message },
        ]);
      }
    } finally {
      setIsRunning(false);
    }
  };

  const handleStop = () => {
    abortControllerRef.current?.abort();
    setIsRunning(false);
    setStatus('ABORTED');
  };

  return (
    <div style={styles.page}>
      <Header status={status} />
      <div style={styles.grid}>
        <InputPanel
          requirement={requirement}
          setRequirement={setRequirement}
          testSuite={testSuite}
          setTestSuite={setTestSuite}
          maxRetries={maxRetries}
          setMaxRetries={setMaxRetries}
          isRunning={isRunning}
          onRun={handleRun}
          onStop={handleStop}
        />
        <div style={styles.column}>
          <ExecutionLog steps={steps} />
          <OutputPanel finalCode={finalCode} judgeReport={judgeReport} />
        </div>
      </div>
    </div>
  );
}
