import { io } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:5000';

export const socket = io(SOCKET_URL, {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});

// Connection event listeners
socket.on('connect', () => {
  console.log('✅ WebSocket connected:', socket.id);
});

socket.on('disconnect', (reason) => {
  console.log('❌ WebSocket disconnected:', reason);
});

socket.on('connect_error', (error) => {
  console.error('🔴 WebSocket connection error:', error.message);
});

socket.on('connected', (data) => {
  console.log('📡 Server confirmed connection:', data);
});

export default socket;
