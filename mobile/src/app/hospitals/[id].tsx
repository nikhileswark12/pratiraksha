import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { useState, useEffect } from 'react';

export default function HospitalDetailScreen() {
  const { id } = useLocalSearchParams();
  const [hospital, setHospital] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`http://localhost:8000/api/v1/hospitals/${id}/`, {
      headers: {
        'Accept': 'application/json',
      }
    })
      .then(response => {
        if (!response.ok) throw new Error('Failed to fetch hospital details');
        return response.json();
      })
      .then(json => {
        setHospital(json);
        setLoading(false);
      })
      .catch(error => {
        console.error(error);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" /></View>;
  }

  if (!hospital) {
    return <View style={styles.center}><Text>Hospital not found.</Text></View>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{hospital.name}</Text>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Status</Text>
        <Text style={{
          color: hospital.status === 'CRITICAL' ? 'red' : 
                 hospital.status === 'MODERATE' ? 'orange' : 'green'
        }}>
          {hospital.status}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Capacity</Text>
        <Text>Occupied: {hospital.current_occupancy}</Text>
        <Text>Total: {hospital.total_capacity}</Text>
        <Text>Utilization: {((hospital.current_occupancy / (hospital.total_capacity || 1)) * 100).toFixed(1)}%</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Contact Info</Text>
        <Text>Phone: {hospital.contact_number || 'N/A'}</Text>
        <Text>Email: {hospital.email || 'N/A'}</Text>
        <Text>Address: {hospital.address}, {hospital.zip_code}</Text>
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
    padding: 15,
    marginBottom: 15,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 2
  },
  cardTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 10 }
});
