import React from 'react';
import './ActionButtons.css';

const ActionButtons = ({ actions, onActionClick }) => {
  if (!actions || actions.length === 0) {
    return null;
  }

  return (
    <div className="action-buttons-container">
      {actions.map((action, index) => {
        // Handle both object format {label: "...", value: "..."} and key-value pairs
        const label = action.label || action.key || Object.values(action)[0] || `Option ${index + 1}`;
        const value = action.value || action.key || Object.keys(action)[0] || action;

        return (
          <button
            key={index}
            className="action-button"
            onClick={() => onActionClick && onActionClick(value, label)}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
};

export default ActionButtons;

