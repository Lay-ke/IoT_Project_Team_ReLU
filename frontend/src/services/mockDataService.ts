import { ConveyorBatchList, ConveyorReading, HealthStatus } from "@/types/conveyor";

const API_ENDPOINT = import.meta.env.VITE_SENSOR_READINGS_ENDPOINT;

export class DataService {
  private static async fetchData(): Promise<ConveyorReading[]> {
    try {
      const response = await fetch(API_ENDPOINT);
      if (!response.ok) {
        throw new Error(`Failed to fetch sensor data: ${response.statusText}`);
      }
      const batchList: ConveyorBatchList = await response.json();

      const allReadings = batchList.flatMap(batch => batch.content);

      // Sort by timestamp to ensure data is in chronological order
      allReadings.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

      return allReadings;
    } catch (error) {
      console.error("Error fetching or processing data:", error);
      throw error;
    }
  }

  static async fetchLatestRawData(): Promise<ConveyorReading | null> {
    const data = await this.fetchData();
    if (data.length === 0) {
      return null;
    }
    return data[data.length - 1];
  }

  static async fetchHistoricalData(): Promise<ConveyorReading[]> {
    const allData = await this.fetchData();
    if (allData.length === 0) {
      return [];
    }

    // Downsample data to a reasonable number of points for charting
    const desiredPoints = 100;
    const step = Math.max(1, Math.floor(allData.length / desiredPoints));
    const sampledData = [];
    for (let i = 0; i < allData.length; i += step) {
      sampledData.push(allData[i]);
    }
    return sampledData;
  }

  static getHealthStatus(fault: string): HealthStatus {
    if (fault === "normal") return "healthy";
    // For now, treat any detected fault as critical. This can be refined.
    return "critical";
  }
}
