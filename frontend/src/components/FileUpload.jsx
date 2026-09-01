import React from 'react';
import { Upload } from 'lucide-react';

export const FileUpload = ({
  accept,
  onFileSelect,
  selectedFile,
  title = 'Click or Drag & Drop File Here',
  subtitle = 'Select file from your device',
  icon: Icon = Upload,
}) => {
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect({ target: { files: e.dataTransfer.files } });
    }
  };

  return (
    <label
      className="dropzone"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept={accept}
        onChange={onFileSelect}
        style={{ display: 'none' }}
      />
      <Icon className="dropzone-icon" size={32} />
      <p style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{title}</p>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-subtle)' }}>
        {selectedFile ? selectedFile.name : subtitle}
      </span>
    </label>
  );
};

export default FileUpload;
