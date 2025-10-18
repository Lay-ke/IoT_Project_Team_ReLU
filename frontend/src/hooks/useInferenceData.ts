import { InferenceRecordList } from '@/types/conveyor';
import { useEffect, useState } from 'react';



export function useInferenceData() {
  const [data, setData] = useState<InferenceRecordList>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      const url = import.meta.env.VITE_INFERENCE_ENDPOINT;

      try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch inference data: ${response.statusText}`);
        }
        const jsonData = await response.json();
        setData(jsonData);
      } catch (e) {
        setError(e instanceof Error ? e : new Error('An unknown error occurred'));
      } finally {
        setIsLoading(false);
      }
    };

    fetchData(); // Fetch data on initial render

    const intervalId = setInterval(fetchData, 60000); // Refetch every 60 seconds

    return () => clearInterval(intervalId); // Cleanup interval on component unmount
  }, []);

  return { data, isLoading, error };
}
