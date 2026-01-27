import api from './api';

export const cameraService = {
  // Get all cameras from backend
  async getAll() {
    try {
      const response = await api.get('/cameras');
      return response.data || [];
    } catch (error) {
      console.error('Failed to load cameras:', error);
      return [];
    }
  },

  // Get camera by ID
  async getById(id) {
    const response = await api.get(`/cameras/${id}`);
    return response.data;
  },

  // Add new camera
  async add(cameraData) {
    const payload = {
      name: cameraData.name,
      rtsp_url: cameraData.rtsp,
      area_name: cameraData.area,
      max_capacity: parseInt(cameraData.maxCap) || 10,
      is_active: true
    };
    
    const response = await api.post('/cameras', payload);
    return response.data;
  },

  // Update camera
  async update(id, cameraData) {
    const payload = {
      name: cameraData.name,
      rtsp_url: cameraData.rtsp,
      area_name: cameraData.area,
      max_capacity: parseInt(cameraData.maxCap) || 10
    };
    
    const response = await api.put(`/cameras/${id}`, payload);
    return response.data;
  },

  // Delete camera
  async delete(id) {
    const response = await api.delete(`/cameras/${id}`);
    return response.success;
  },

  // Get occupancy stats
  async getOccupancyStats() {
    const response = await api.get('/occupancy/stats');
    return response.data || [];
  },

  // Get video stream URL
  getVideoStreamUrl(cameraUuid) {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
    return `${baseUrl}/video_feed/${cameraUuid}`;
  }
};
