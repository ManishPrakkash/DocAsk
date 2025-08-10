import { create } from 'zustand';
import { DocumentState, Document, DocumentAnalysis, DocumentStatus } from '@/types';
import { documentAPI, handleAPIError } from '@/lib/api';
import toast from 'react-hot-toast';

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  currentDocument: null,
  isLoading: false,
  uploadProgress: 0,

  fetchDocuments: async () => {
    set({ isLoading: true });
    
    try {
      const documents = await documentAPI.getDocuments();
      set({ documents, isLoading: false });
    } catch (error) {
      const errorMessage = handleAPIError(error);
      toast.error(`Failed to fetch documents: ${errorMessage}`);
      set({ isLoading: false });
      throw error;
    }
  },

  uploadDocument: async (file: File): Promise<number> => {
    set({ uploadProgress: 0 });
    
    try {
      const response = await documentAPI.uploadDocument(file, (progress) => {
        set({ uploadProgress: progress });
      });
      
      // Refresh documents list
      await get().fetchDocuments();
      
      toast.success('Document uploaded successfully! Processing will begin shortly.');
      set({ uploadProgress: 0 });
      
      return response.document_id;
    } catch (error) {
      const errorMessage = handleAPIError(error);
      toast.error(`Upload failed: ${errorMessage}`);
      set({ uploadProgress: 0 });
      throw error;
    }
  },

  fetchDocumentAnalysis: async (id: number) => {
    set({ isLoading: true });
    
    try {
      const analysis = await documentAPI.getDocumentAnalysis(id);
      set({ currentDocument: analysis, isLoading: false });
    } catch (error) {
      const errorMessage = handleAPIError(error);
      toast.error(`Failed to fetch analysis: ${errorMessage}`);
      set({ isLoading: false });
      throw error;
    }
  },

  pollDocumentStatus: async (id: number): Promise<DocumentStatus> => {
    try {
      const status = await documentAPI.getDocumentStatus(id);
      
      // Update the document in the list with new status
      const { documents } = get();
      const updatedDocuments = documents.map(doc => 
        doc.id === id 
          ? { 
              ...doc, 
              status: status.status, 
              total_clauses_found: status.total_clauses_found,
              error_message: status.error_message 
            }
          : doc
      );
      
      set({ documents: updatedDocuments });
      
      return status;
    } catch (error) {
      const errorMessage = handleAPIError(error);
      console.error(`Failed to poll document status: ${errorMessage}`);
      throw error;
    }
  },

  deleteDocument: async (id: number) => {
    try {
      await documentAPI.deleteDocument(id);
      
      // Remove document from state
      const { documents } = get();
      const updatedDocuments = documents.filter(doc => doc.id !== id);
      set({ documents: updatedDocuments });
      
      // Clear current document if it's the one being deleted
      const { currentDocument } = get();
      if (currentDocument?.document.id === id) {
        set({ currentDocument: null });
      }
      
      toast.success('Document deleted successfully');
    } catch (error) {
      const errorMessage = handleAPIError(error);
      toast.error(`Failed to delete document: ${errorMessage}`);
      throw error;
    }
  },
}));