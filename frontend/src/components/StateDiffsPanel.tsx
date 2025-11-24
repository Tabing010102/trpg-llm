import React from 'react';
import type { StateDiff } from '../types/api';

interface StateDiffsPanelProps {
  diffs: StateDiff[];
}

const StateDiffsPanel: React.FC<StateDiffsPanelProps> = ({ diffs }) => {
  return (
    <div className="state-diffs-panel">
      <h3>Recent State Changes</h3>
      {diffs.length === 0 ? (
        <p className="text-muted">No recent changes</p>
      ) : (
        <div className="diffs-list">
          {diffs.map((diff, idx) => (
            <div key={idx} className="diff-item">
              <div className="diff-path">
                <span className="label">Path:</span>
                <code>{diff.path}</code>
              </div>
              <div className="diff-operation">
                <span className="label">Operation:</span>
                <span className={`operation-badge operation-${diff.operation}`}>
                  {diff.operation}
                </span>
              </div>
              <div className="diff-value">
                <span className="label">Value:</span>
                <code>{JSON.stringify(diff.value)}</code>
              </div>
              {diff.previous_value !== undefined && (
                <div className="diff-previous">
                  <span className="label">Previous:</span>
                  <code>{JSON.stringify(diff.previous_value)}</code>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StateDiffsPanel;
