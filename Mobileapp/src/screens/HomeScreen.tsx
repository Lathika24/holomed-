import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import DocumentPicker from 'react-native-document-picker';
import axios from 'axios';
import { useNavigation } from '@react-navigation/native';
import { useAuthStore } from '../store/authStore';

interface Model {
  id: number;
  name: string;
  file_path: string;
  file_format: string;
  created_at: string;
}

const API_URL = 'http://localhost:8000'; // Change to your backend URL

export default function HomeScreen() {
  const navigation = useNavigation();
  const { token, clearAuth } = useAuthStore();
  const [uploading, setUploading] = useState(false);
  const queryClient = useQueryClient();

  const { data: models, isLoading } = useQuery<Model[]>({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/api/models`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    },
    enabled: !!token,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: any) => {
      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: file.type,
        name: file.name,
      } as any);

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
      Alert.alert('Success', 'Model uploaded successfully');
    },
    onError: (error: any) => {
      setUploading(false);
      Alert.alert('Error', error.response?.data?.detail || 'Upload failed');
    },
  });

  const handleUpload = async () => {
    try {
      const result = await DocumentPicker.pick({
        type: [DocumentPicker.types.allFiles],
        copyTo: 'cachesDirectory',
      });

      if (result[0]) {
        setUploading(true);
        uploadMutation.mutate(result[0]);
      }
    } catch (err) {
      if (DocumentPicker.isCancel(err)) {
        // User cancelled
      } else {
        Alert.alert('Error', 'Failed to pick file');
      }
    }
  };

  const handleModelSelect = (model: Model) => {
    navigation.navigate('HoloViewer' as never, { model } as never);
  };

  const handleLogout = () => {
    clearAuth();
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Your 3D Models</Text>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={styles.uploadButton}
        onPress={handleUpload}
        disabled={uploading}
      >
        {uploading ? (
          <ActivityIndicator color="#000" />
        ) : (
          <Text style={styles.uploadButtonText}>Upload 3D Model</Text>
        )}
      </TouchableOpacity>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#00ffff" />
        </View>
      ) : !models || models.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>No models yet</Text>
          <Text style={styles.emptySubtext}>Upload your first 3D model</Text>
        </View>
      ) : (
        <FlatList
          data={models}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.modelCard}
              onPress={() => handleModelSelect(item)}
            >
              <Text style={styles.modelName}>{item.name}</Text>
              <Text style={styles.modelFormat}>{item.file_format.toUpperCase()}</Text>
            </TouchableOpacity>
          )}
          contentContainerStyle={styles.list}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000000',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00ffff',
  },
  logoutButton: {
    padding: 8,
  },
  logoutText: {
    color: '#00ffff',
    fontSize: 16,
  },
  uploadButton: {
    backgroundColor: '#00ffff',
    padding: 16,
    margin: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  uploadButtonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: 'bold',
  },
  list: {
    padding: 16,
  },
  modelCard: {
    backgroundColor: '#1a1a1a',
    padding: 16,
    marginBottom: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333333',
  },
  modelName: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  modelFormat: {
    color: '#888888',
    fontSize: 14,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    color: '#ffffff',
    fontSize: 18,
    marginBottom: 8,
  },
  emptySubtext: {
    color: '#888888',
    fontSize: 14,
  },
});
