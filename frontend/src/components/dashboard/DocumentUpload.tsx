import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import { useDocumentStore } from '@/stores/documentStore';
import LoadingSpinner from '../ui/LoadingSpinner';

const DocumentUpload: React.FC = () => {
  const { uploadDocument, uploadProgress } = useDocumentStore();
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploadedFiles(acceptedFiles);
    setIsUploading(true);

    try {
      for (const file of acceptedFiles) {
        await uploadDocument(file);
      }
      setUploadedFiles([]);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setIsUploading(false);
    }
  }, [uploadDocument]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc']
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
    disabled: isUploading
  });

  const removeFile = (fileToRemove: File) => {
    setUploadedFiles(prev => prev.filter(file => file !== fileToRemove));
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors duration-200
          ${isDragActive 
            ? 'border-primary-400 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        {isUploading ? (
          <div className="space-y-4">
            <LoadingSpinner size="lg" />
            <div>
              <p className="text-lg font-medium text-gray-900">Uploading...</p>
              <div className="mt-2 bg-gray-200 rounded-full h-2 w-full max-w-xs mx-auto">
                <div 
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-1">{uploadProgress}% complete</p>
            </div>
          </div>
        ) : (
          <>
            <Upload className="h-10 w-10 text-gray-400 mx-auto mb-4" />
            <div>
              <p className="text-lg font-medium text-gray-900">
                {isDragActive ? 'Drop your document here' : 'Upload legal document'}
              </p>
              <p className="text-gray-600 mt-1">
                Drag and drop a PDF or DOCX file, or click to browse
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Maximum file size: 10MB
              </p>
            </div>
          </>
        )}
      </div>

      {/* File Rejections */}
      {fileRejections.length > 0 && (
        <div className="space-y-2">
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex items-center">
                <X className="h-4 w-4 text-red-400 mr-2" />
                <p className="text-sm text-red-800">
                  <span className="font-medium">{file.name}</span> - {errors[0]?.message}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Uploaded Files Preview */}
      {uploadedFiles.length > 0 && !isUploading && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-900">Ready to upload:</h4>
          {uploadedFiles.map((file, index) => (
            <div key={index} className="flex items-center justify-between bg-gray-50 rounded-md p-3">
              <div className="flex items-center">
                <FileText className="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(file);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Success Message */}
      {uploadProgress === 100 && !isUploading && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <div className="flex items-center">
            <CheckCircle className="h-4 w-4 text-green-400 mr-2" />
            <p className="text-sm text-green-800">
              Document uploaded successfully! Processing will begin shortly.
            </p>
          </div>
        </div>
      )}

      {/* Supported Formats */}
      <div className="text-xs text-gray-500">
        <p className="font-medium mb-1">Supported formats:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>PDF documents (.pdf)</li>
          <li>Microsoft Word documents (.docx, .doc)</li>
        </ul>
      </div>
    </div>
  );
};

export default DocumentUpload;