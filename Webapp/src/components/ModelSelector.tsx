'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

interface Model {
  id: number;
  name: string;
  file_path: string;
  file_format: string;
  created_at: string;
}

interface ModelSelectorProps {
  onSelect: (modelUrl: string) => void;
  isAuthenticated: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ModelSelector({ onSelect, isAuthenticated }: ModelSelectorProps) {
  const [uploading, setUploading] = useState(false);
  const { token } = useAuthStore();
  const queryClient = useQueryClient();

  // Fetch user's models
  const { data: models, isLoading } = useQuery<Model[]>({
    queryKey: ['models'],
    queryFn: async () => {
      if (!token) return [];
      const response = await axios.get(`${API_URL}/api/models`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      return response.data;
    },
    enabled: isAuthenticated && !!token,
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post(`${API_URL}/api/models/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      setUploading(false);
    },
    onError: () => {
      setUploading(false);
    },
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    uploadMutation.mutate(file);
  };

  const handleModelSelect = (model: Model) => {
    // Construct full URL for the model
    const modelUrl = model.file_path.startsWith('http') 
      ? model.file_path 
      : `${API_URL}/${model.file_path}`;
    onSelect(modelUrl);
  };

  // Default model for non-authenticated users
  const useDefaultModel = () => {
    // You can use a default model URL or a sample model
    onSelect('https://threejs.org/examples/models/gltf/Duck/glTF/Duck.gltf');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full">
        <h1 className="text-5xl font-bold text-center mb-4 bg-gradient-to-r from-cyan-400 to-white bg-clip-text text-transparent">
          HoloMed
        </h1>
        <p className="text-center text-gray-400 mb-12">
          Holographic Medical Visualization with Hand Tracking
        </p>

        {!isAuthenticated ? (
          <div className="bg-gray-900 rounded-lg p-8 text-center">
            <p className="text-gray-400 mb-4">
              Login to upload and manage your 3D models, or try with a sample model
            </p>
            <button
              onClick={useDefaultModel}
              className="px-6 py-3 bg-cyan-500 text-black rounded-lg hover:bg-cyan-400 transition-colors font-semibold"
            >
              Try Sample Model
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Upload Section */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-cyan-400">Upload 3D Model</h2>
              <div className="flex items-center gap-4">
                <label className="px-6 py-3 bg-cyan-500 text-black rounded-lg hover:bg-cyan-400 transition-colors cursor-pointer font-semibold">
                  {uploading ? 'Uploading...' : 'Choose File'}
                  <input
                    type="file"
                    className="hidden"
                    accept=".stl,.obj,.ply,.vtk,.gltf,.glb"
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </label>
                <span className="text-gray-400 text-sm">
                  Supported: STL, OBJ, PLY, VTK, GLTF, GLB
                </span>
              </div>
            </div>

            {/* Models List */}
            <div className="bg-gray-900 rounded-lg p-6">
              <h2 className="text-2xl font-semibold mb-4 text-cyan-400">Your Models</h2>
              
              {isLoading ? (
                <div className="text-center py-8 text-gray-400">Loading models...</div>
              ) : !models || models.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  No models yet. Upload your first 3D model above.
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {models.map((model) => (
                    <button
                      key={model.id}
                      onClick={() => handleModelSelect(model)}
                      className="bg-gray-800 hover:bg-gray-700 rounded-lg p-4 text-left transition-colors border border-gray-700 hover:border-cyan-500"
                    >
                      <div className="font-semibold text-white mb-2">{model.name}</div>
                      <div className="text-sm text-gray-400">
                        Format: {model.file_format.toUpperCase()}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(model.created_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
