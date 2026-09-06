import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';
import { useState, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import { router } from 'expo-router';

export default function DashboardScreen() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = await SecureStore.getItemAsync('userToken');
        if (!token) {
          router.replace('/login');
          return;
        }

        const response = await fetch('http://localhost:8000/api/v1/analytics/overview/', {
          headers: {
            'Accept': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.status === 401 || response.status === 403) {
          await SecureStore.deleteItemAsync('userToken');
          router.replace('/login');
          return;
        }

        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const json = await response.json();
        setData(json);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" /></View>;
  }

  if (!data) {
    return <View style={styles.center}><Text>Failed to load data.</Text></View>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Network Dashboard</Text>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Capacity Overview</Text>
        <Text>Total Beds: {data.network_capacity?.total_capacity}</Text>
        <Text>Occupied: {data.network_capacity?.current_occupancy}</Text>
        <Text>Utilization: {data.network_capacity?.occupancy_rate}%</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Status Breakdown</Text>
        <Text>Normal: {data.status_breakdown?.NORMAL || 0}</Text>
        <Text>Moderate: {data.status_breakdown?.MODERATE || 0}</Text>
        <Text style={{color: 'red'}}>Critical: {data.status_breakdown?.CRITICAL || 0}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  container: { flex: 1, padding: 20, backgroundColor: '#f5f5f5' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 20 },
  card: { 
    backgroundColor: '#fff', 
    padding: 20, 
    borderRadius: 8, 
    marginBottom: 15,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 2
  },
  cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 10 }
});
