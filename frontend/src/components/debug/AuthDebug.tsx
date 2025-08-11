import React from 'react';
import { useAuthStore } from '../../stores/authStore';

const AuthDebug: React.FC = () => {
  const { user, token, isAuthenticated, isLoading } = useAuthStore();
  
  const localStorageToken = localStorage.getItem('auth_token');

  return (
    <div className="fixed top-4 right-4 bg-white p-4 rounded-lg shadow-lg border max-w-sm z-50">
      <h3 className="font-bold text-sm mb-2">Auth Debug Info</h3>
      <div className="text-xs space-y-1">
        <div><strong>isAuthenticated:</strong> {isAuthenticated ? 'true' : 'false'}</div>
        <div><strong>isLoading:</strong> {isLoading ? 'true' : 'false'}</div>
        <div><strong>Token in store:</strong> {token ? 'Present' : 'None'}</div>
        <div><strong>Token in localStorage:</strong> {localStorageToken ? 'Present' : 'None'}</div>
        <div><strong>User:</strong> {user ? user.email : 'None'}</div>
        <div><strong>User ID:</strong> {user ? user.id : 'None'}</div>
      </div>
    </div>
  );
};

export default AuthDebug;
