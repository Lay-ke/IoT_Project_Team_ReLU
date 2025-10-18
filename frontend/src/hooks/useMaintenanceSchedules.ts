import { useState, useEffect } from 'react';
import { MaintenanceSchedule } from '@/types/conveyor';

const API_ENDPOINT = import.meta.env.VITE_MAINTENANCE_SCHEDULES_ENDPOINT;

export function useMaintenanceSchedules() {
  const [data, setData] = useState<MaintenanceSchedule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(API_ENDPOINT);
        if (!response.ok) {
          throw new Error(`Failed to fetch maintenance schedules: ${response.statusText}`);
        }
        const jsonData: MaintenanceSchedule[] = await response.json();
        setData(jsonData);
      } catch (e) {
        setError(e instanceof Error ? e : new Error('An unknown error occurred'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000); // Refetch every 60 seconds

    return () => clearInterval(interval);
  }, []);

  return { data, isLoading, error };
}
